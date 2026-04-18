"""Rule-based anomaly detection.

If N events with the same signature occur within the rolling window, open
(or update) an Alert. Severity rises with event count.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.config import ANOMALY_THRESHOLD, ANOMALY_WINDOW_SECONDS
from backend.connectors.mock_sentry import SentryEvent
from backend.db import Event, Alert
from backend.events_bus import bus


def _severity(count: int) -> str:
    if count >= 15:
        return "critical"
    if count >= 8:
        return "high"
    if count >= 3:
        return "medium"
    return "low"


def ingest_event(db: Session, event: SentryEvent, fault_injected_at: datetime | None = None) -> tuple[Event, Alert | None]:
    signature = event.signature()
    row = Event(
        service=event.service,
        exception_type=event.exception_type,
        message=event.message,
        stack_trace=event.stack_trace,
        signature=signature,
        payload_json=event.to_json(),
        created_at=event.timestamp,
    )
    db.add(row)
    db.flush()

    # Count events in window
    window_start = datetime.utcnow() - timedelta(seconds=ANOMALY_WINDOW_SECONDS)
    recent_count = (
        db.query(Event)
        .filter(Event.signature == signature, Event.created_at >= window_start)
        .count()
    )

    alert: Alert | None = None
    if recent_count >= ANOMALY_THRESHOLD:
        alert = (
            db.query(Alert)
            .filter(Alert.signature == signature, Alert.status != "resolved")
            .first()
        )
        if alert is None:
            alert = Alert(
                service=event.service,
                exception_type=event.exception_type,
                signature=signature,
                severity=_severity(recent_count),
                status="open",
                event_count=recent_count,
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                detected_at=datetime.utcnow(),
                fault_injected_at=fault_injected_at,
            )
            db.add(alert)
            db.flush()
            bus.publish("alert.created", {"id": alert.id, "signature": signature, "severity": alert.severity})
        else:
            alert.event_count = recent_count
            alert.last_seen = event.timestamp
            alert.severity = _severity(recent_count)
            bus.publish("alert.updated", {"id": alert.id, "count": recent_count})

        row.alert_id = alert.id

    db.commit()
    return row, alert
