import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import Alert, Diagnosis, get_session
from backend.rca.llm_rca import diagnose

router = APIRouter(prefix="/api", tags=["diagnosis"])


def _serialize(d: Diagnosis) -> dict:
    return {
        "id": d.id,
        "alert_id": d.alert_id,
        "root_cause": d.root_cause,
        "contributing_factors": json.loads(d.contributing_factors or "[]"),
        "confidence": d.confidence,
        "latency_ms": d.latency_ms,
        "created_at": d.created_at.isoformat(),
    }


@router.post("/alerts/{alert_id}/diagnose")
def run_diagnosis(alert_id: int, db: Session = Depends(get_session)):
    alert = db.query(Alert).get(alert_id)
    if not alert:
        raise HTTPException(404)
    d = diagnose(db, alert)
    return _serialize(d)


@router.get("/alerts/{alert_id}/diagnosis")
def get_diagnosis(alert_id: int, db: Session = Depends(get_session)):
    d = db.query(Diagnosis).filter_by(alert_id=alert_id).first()
    if not d:
        raise HTTPException(404)
    return _serialize(d)
