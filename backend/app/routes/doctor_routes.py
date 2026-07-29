from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.database import get_db, User, Prediction, create_notification, add_audit_log
from app.utils.security import require_role
from app.utils.serializers import serialize_prediction, serialize_user

router = APIRouter(prefix="/doctor", tags=["Doctor"])


class ReviewRequest(BaseModel):
    remarks: str = Field(min_length=2, max_length=5000)
    recommendation: str | None = Field(default=None, max_length=5000)
    follow_up_date: str | None = None
    review_status: str = "completed"


@router.get("/dashboard")
def doctor_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    reports = db.query(Prediction).filter(Prediction.assigned_doctor_id == current_user.id)
    patient_count = reports.with_entities(Prediction.patient_id).distinct().count()
    pending_values = ["pending_review", "needs_attention", "under_review"]
    return {
        "total_patients": patient_count,
        "total_reports": reports.count(),
        "pending_reviews": reports.filter(Prediction.review_status.in_(pending_values)).count(),
        "completed_reviews": reports.filter(Prediction.review_status == "completed").count(),
        "high_risk_cases": reports.filter(Prediction.risk_level.in_(["high", "review_required"])).count(),
        "recent_uploads": [
            serialize_prediction(item) for item in reports.options(joinedload(Prediction.patient))
            .order_by(Prediction.created_at.desc()).limit(5).all()
        ],
    }


@router.get("/reports")
def doctor_reports(
    search: str | None = None,
    review_status: str | None = None,
    risk_level: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    query = db.query(Prediction).options(joinedload(Prediction.patient)).filter(
        Prediction.assigned_doctor_id == current_user.id
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Prediction.patient_name.ilike(term), Prediction.predicted_class.ilike(term)))
    if review_status:
        query = query.filter(Prediction.review_status == review_status)
    if risk_level:
        query = query.filter(Prediction.risk_level == risk_level)
    return [serialize_prediction(item) for item in query.order_by(Prediction.created_at.desc()).all()]


@router.get("/patients")
def assigned_patients(
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    patient_ids = db.query(Prediction.patient_id).filter(
        Prediction.assigned_doctor_id == current_user.id,
        Prediction.patient_id.is_not(None),
    ).distinct()
    query = db.query(User).filter(User.id.in_(patient_ids))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))
    patients = []
    for patient in query.order_by(User.name).all():
        data = serialize_user(patient)
        data["report_count"] = db.query(Prediction).filter(
            Prediction.patient_id == patient.id,
            Prediction.assigned_doctor_id == current_user.id,
        ).count()
        patients.append(data)
    return patients


@router.get("/patients/{patient_id}")
def patient_profile(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    has_assignment = db.query(Prediction).filter(
        Prediction.patient_id == patient_id,
        Prediction.assigned_doctor_id == current_user.id,
    ).first()
    if not has_assignment:
        raise HTTPException(status_code=403, detail="This patient is not assigned to you")
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return serialize_user(patient)


@router.get("/patients/{patient_id}/compare")
def compare_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    reports = db.query(Prediction).options(joinedload(Prediction.assigned_doctor)).filter(
        Prediction.patient_id == patient_id,
        Prediction.assigned_doctor_id == current_user.id,
    ).order_by(Prediction.created_at.desc()).all()
    if not reports:
        raise HTTPException(status_code=404, detail="No assigned reports found for this patient")
    patient = db.query(User).filter(User.id == patient_id).first()
    return {
        "patient_id": patient_id,
        "patient_name": reports[0].patient_name,
        "patient": serialize_user(patient) if patient else None,
        "reports": [serialize_prediction(item) for item in reports],
        "trend": _build_trend(reports),
    }


def _build_trend(reports: list[Prediction]) -> str:
    if len(reports) < 2:
        return "Only one report is available; a trend cannot yet be calculated."
    latest, previous = reports[0], reports[1]
    change = latest.confidence - previous.confidence
    direction = "increased" if change > 0 else "decreased" if change < 0 else "remained unchanged"
    return (
        f"The latest AI confidence {direction} by {abs(change):.2f} percentage points. "
        "This comparison is informational and must be interpreted by a clinician using the original MRI scans."
    )


@router.put("/reports/{report_id}/review")
def review_report(
    report_id: int,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("doctor")),
):
    if payload.review_status not in {"under_review", "completed"}:
        raise HTTPException(status_code=400, detail="review_status must be under_review or completed")
    prediction = db.query(Prediction).filter(
        Prediction.id == report_id,
        Prediction.assigned_doctor_id == current_user.id,
    ).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Assigned report not found")

    prediction.doctor_remarks = payload.remarks.strip()
    prediction.recommendation = payload.recommendation.strip() if payload.recommendation else None
    prediction.follow_up_date = payload.follow_up_date
    prediction.review_status = payload.review_status
    prediction.reviewed_at = datetime.utcnow() if payload.review_status == "completed" else None
    create_notification(
        db, prediction.patient_id,
        "Doctor review updated",
        f"Report #{prediction.id} is now {prediction.review_status.replace('_', ' ')}.",
        prediction.id,
    )
    add_audit_log(db, current_user, "doctor_review_updated", "prediction", prediction.id)
    db.commit()
    db.refresh(prediction)
    return {"message": "Review saved successfully", "report": serialize_prediction(prediction)}
