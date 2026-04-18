"""LLM-powered remediation generator.

Produces a unified-diff patch that can be applied to the target file.
Patches are *staged* (stored in DB) until the user approves them.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.config import OPENAI_API_KEY, OPENAI_MODEL, SAMPLE_SERVICE_DIR
from backend.db import Alert, Diagnosis, Remediation, Event

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = (
    "You are an expert software engineer generating minimal, safe bug "
    "fixes. Given an incident diagnosis and the current source of the "
    "offending file, produce a corrected version of the file. Respond "
    "ONLY with valid JSON matching this schema: "
    '{"target_file": string (file basename only), '
    '"new_content": string (complete updated file contents), '
    '"rationale": string (1-3 sentences explaining the fix)}'
)


def _pick_target_file(stack_trace: str) -> Path | None:
    for line in stack_trace.splitlines():
        line = line.strip()
        if "sample_service" in line and ".py" in line:
            try:
                path = Path(line.split('"')[1])
                if path.is_file():
                    return path
            except Exception:
                continue
    # Fallback: first .py under sample_service
    if SAMPLE_SERVICE_DIR.is_dir():
        for f in SAMPLE_SERVICE_DIR.glob("*.py"):
            return f
    return None


def _make_diff(old: str, new: str, filename: str) -> str:
    import difflib
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))


def generate(db: Session, alert: Alert) -> Remediation:
    existing = db.query(Remediation).filter_by(alert_id=alert.id).first()
    if existing:
        return existing

    diagnosis = db.query(Diagnosis).filter_by(alert_id=alert.id).first()
    if diagnosis is None:
        raise ValueError("Alert must be diagnosed before remediation")

    latest_event = (
        db.query(Event)
        .filter(Event.signature == alert.signature)
        .order_by(Event.created_at.desc())
        .first()
    )
    if latest_event is None:
        raise ValueError("No events for alert")

    target = _pick_target_file(latest_event.stack_trace)
    if target is None:
        raise ValueError("Could not locate target source file")

    original = target.read_text()
    factors = json.loads(diagnosis.contributing_factors or "[]")

    user_prompt = (
        f"Diagnosis: {diagnosis.root_cause}\n"
        f"Contributing factors: {factors}\n"
        f"Exception: {latest_event.exception_type}: {latest_event.message}\n\n"
        f"File: {target.name}\n"
        f"Current contents:\n```python\n{original}\n```"
    )

    resp = _get_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    parsed = json.loads(resp.choices[0].message.content or "{}")
    new_content = parsed.get("new_content") or ""
    rationale = parsed.get("rationale") or ""

    diff = _make_diff(original, new_content, target.name)

    remediation = Remediation(
        alert_id=alert.id,
        target_file=str(target),
        diff=diff,
        rationale=rationale,
        status="pending",
    )
    db.add(remediation)
    alert.status = "remediated"
    db.commit()
    db.refresh(remediation)

    # Stash the proposed new content alongside the diff for deterministic apply
    _staged_content[remediation.id] = new_content
    return remediation


_staged_content: dict[int, str] = {}


def apply_remediation(db: Session, remediation: Remediation) -> None:
    new_content = _staged_content.get(remediation.id)
    if new_content is None:
        raise ValueError("No staged content; re-generate the remediation")
    Path(remediation.target_file).write_text(new_content)
    remediation.status = "applied"
    remediation.applied_at = datetime.utcnow()
    alert = db.query(Alert).get(remediation.alert_id)
    if alert is not None:
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
    db.commit()
