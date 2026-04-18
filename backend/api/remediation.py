from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import Alert, Remediation, get_session
from backend.remediation.generator import generate, apply_remediation

router = APIRouter(prefix="/api", tags=["remediation"])


def _serialize(r: Remediation) -> dict:
    return {
        "id": r.id,
        "alert_id": r.alert_id,
        "target_file": r.target_file,
        "diff": r.diff,
        "rationale": r.rationale,
        "status": r.status,
        "created_at": r.created_at.isoformat(),
        "applied_at": r.applied_at.isoformat() if r.applied_at else None,
    }


@router.post("/alerts/{alert_id}/remediate")
def run_remediation(alert_id: int, db: Session = Depends(get_session)):
    alert = db.query(Alert).get(alert_id)
    if not alert:
        raise HTTPException(404)
    r = generate(db, alert)
    return _serialize(r)


@router.get("/alerts/{alert_id}/remediation")
def get_remediation(alert_id: int, db: Session = Depends(get_session)):
    r = db.query(Remediation).filter_by(alert_id=alert_id).first()
    if not r:
        raise HTTPException(404)
    return _serialize(r)


@router.post("/remediations/{remediation_id}/approve")
def approve(remediation_id: int, db: Session = Depends(get_session)):
    r = db.query(Remediation).get(remediation_id)
    if not r:
        raise HTTPException(404)
    if r.status == "applied":
        return _serialize(r)
    r.status = "approved"
    db.commit()
    apply_remediation(db, r)
    db.refresh(r)
    return _serialize(r)


@router.post("/remediations/{remediation_id}/reject")
def reject(remediation_id: int, db: Session = Depends(get_session)):
    r = db.query(Remediation).get(remediation_id)
    if not r:
        raise HTTPException(404)
    r.status = "rejected"
    db.commit()
    return _serialize(r)
