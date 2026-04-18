import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.connectors.mock_sentry import SentryEvent
from backend.db import Alert, Event, get_session
from backend.detection.engine import ingest_event

router = APIRouter(prefix="/api", tags=["alerts"])


@router.post("/ingest")
def ingest(event: SentryEvent, fault_injected_at: datetime | None = None, db: Session = Depends(get_session)):
    row, alert = ingest_event(db, event, fault_injected_at=fault_injected_at)
    return {"event_id": row.id, "alert_id": alert.id if alert else None}


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_session)):
    rows = db.query(Alert).order_by(Alert.detected_at.desc()).all()
    return [
        {
            "id": a.id,
            "service": a.service,
            "exception_type": a.exception_type,
            "signature": a.signature,
            "severity": a.severity,
            "status": a.status,
            "event_count": a.event_count,
            "first_seen": a.first_seen.isoformat(),
            "last_seen": a.last_seen.isoformat(),
            "detected_at": a.detected_at.isoformat(),
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }
        for a in rows
    ]


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_session)):
    a = db.query(Alert).get(alert_id)
    if not a:
        raise HTTPException(404)
    events = (
        db.query(Event)
        .filter(Event.signature == a.signature)
        .order_by(Event.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "id": a.id,
        "service": a.service,
        "exception_type": a.exception_type,
        "signature": a.signature,
        "severity": a.severity,
        "status": a.status,
        "event_count": a.event_count,
        "first_seen": a.first_seen.isoformat(),
        "last_seen": a.last_seen.isoformat(),
        "detected_at": a.detected_at.isoformat(),
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        "fault_injected_at": a.fault_injected_at.isoformat() if a.fault_injected_at else None,
        "events": [
            {
                "id": e.id,
                "message": e.message,
                "stack_trace": e.stack_trace,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }
