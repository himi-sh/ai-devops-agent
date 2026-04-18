"""LLM-powered root cause analysis."""
from __future__ import annotations

import json
import time
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.config import OPENAI_API_KEY, OPENAI_MODEL, SAMPLE_SERVICE_DIR
from backend.db import Alert, Diagnosis, Event

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "You are an expert SRE assistant performing incident root-cause "
    "analysis. Given an exception stack trace and surrounding context, "
    "identify the most likely root cause in clear, human-friendly terms. "
    "Respond ONLY with valid JSON matching this schema: "
    '{"root_cause": string, "contributing_factors": string[], "confidence": number between 0 and 1}'
)


def _related_source(exception_type: str, stack_trace: str) -> str:
    """Return contents of any referenced sample_service files (best-effort)."""
    snippets: list[str] = []
    for line in stack_trace.splitlines():
        line = line.strip()
        if "sample_service" in line and ".py" in line:
            # e.g. File "/.../sample_service/buggy_service.py", line 7, in compute_total
            try:
                path_part = line.split('"')[1]
                from pathlib import Path
                p = Path(path_part)
                if p.is_file():
                    snippets.append(f"--- {p.name} ---\n{p.read_text()}")
            except Exception:
                continue
    # Fallback: load any .py from SAMPLE_SERVICE_DIR
    if not snippets and SAMPLE_SERVICE_DIR.is_dir():
        for f in SAMPLE_SERVICE_DIR.glob("*.py"):
            snippets.append(f"--- {f.name} ---\n{f.read_text()}")
    return "\n\n".join(snippets)


def diagnose(db: Session, alert: Alert) -> Diagnosis:
    existing = db.query(Diagnosis).filter_by(alert_id=alert.id).first()
    if existing:
        return existing

    # Gather recent events for this alert
    events = (
        db.query(Event)
        .filter(Event.signature == alert.signature)
        .order_by(Event.created_at.desc())
        .limit(3)
        .all()
    )
    if not events:
        raise ValueError(f"No events for alert {alert.id}")

    latest = events[0]
    source_ctx = _related_source(latest.exception_type, latest.stack_trace)

    user_prompt = (
        f"Service: {alert.service}\n"
        f"Exception: {latest.exception_type}: {latest.message}\n"
        f"Occurrences in window: {alert.event_count}\n\n"
        f"Stack trace:\n{latest.stack_trace}\n\n"
        f"Related source:\n{source_ctx or '(none available)'}"
    )

    t0 = time.monotonic()
    resp = _get_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    latency_ms = int((time.monotonic() - t0) * 1000)

    raw = resp.choices[0].message.content or "{}"
    parsed = json.loads(raw)

    diagnosis = Diagnosis(
        alert_id=alert.id,
        root_cause=parsed.get("root_cause", "Unknown"),
        contributing_factors=json.dumps(parsed.get("contributing_factors", [])),
        confidence=float(parsed.get("confidence", 0.5)),
        latency_ms=latency_ms,
    )
    db.add(diagnosis)
    alert.status = "diagnosed"
    db.commit()
    db.refresh(diagnosis)
    return diagnosis
