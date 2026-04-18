from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db import Alert, Diagnosis, Remediation, get_session

router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics")
def metrics(db: Session = Depends(get_session)):
    alerts = db.query(Alert).all()
    detection_latencies: list[float] = []
    mttr_values: list[float] = []
    diagnosis_latencies: list[int] = []
    resolved = 0

    for a in alerts:
        if a.fault_injected_at:
            detection_latencies.append((a.detected_at - a.fault_injected_at).total_seconds())
            if a.resolved_at:
                mttr_values.append((a.resolved_at - a.fault_injected_at).total_seconds())
        if a.status == "resolved":
            resolved += 1

    for d in db.query(Diagnosis).all():
        diagnosis_latencies.append(d.latency_ms)

    applied = db.query(Remediation).filter_by(status="applied").count()

    def avg(xs):
        return round(sum(xs) / len(xs), 2) if xs else None

    return {
        "total_alerts": len(alerts),
        "resolved_alerts": resolved,
        "applied_remediations": applied,
        "avg_detection_latency_s": avg(detection_latencies),
        "avg_diagnosis_latency_ms": avg(diagnosis_latencies),
        "avg_mttr_s": avg(mttr_values),
    }
