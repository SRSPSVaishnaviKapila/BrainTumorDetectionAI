from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from app.database import (
    get_db, Prediction, User, Notification, create_notification, add_audit_log, SystemSetting
)
from app.services.image_service import save_uploaded_image
from app.services.ml_service import ml_service
from app.services.pdf_service import generate_prediction_report
from app.utils.security import get_current_user
from app.utils.serializers import serialize_prediction

router = APIRouter(tags=["Predictions"])


def _auto_assign_doctor(db: Session) -> User | None:
    doctors = db.query(User).filter(User.role == "doctor", User.is_active.is_(True)).all()
    if not doctors:
        return None
    return min(
        doctors,
        key=lambda doctor: db.query(Prediction).filter(
            Prediction.assigned_doctor_id == doctor.id,
            Prediction.review_status.in_(["pending_review", "needs_attention", "under_review"]),
        ).count(),
    )


def _can_access(prediction: Prediction, user: User) -> bool:
    if user.role == "admin":
        return True
    if user.role == "doctor":
        return prediction.assigned_doctor_id == user.id
    return prediction.patient_id == user.id


@router.post("/predict")
async def predict_tumor(
    file: UploadFile = File(...),
    patient_name: str | None = Form(None),
    age: int | None = Form(None),
    gender: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="MRI upload from this screen is available to patients only")

    image_path = await save_uploaded_image(file)
    result = ml_service.predict(image_path)
    threshold_setting = db.query(SystemSetting).filter(SystemSetting.key == "confidence_threshold").first()
    try:
        threshold = float(threshold_setting.value) if threshold_setting else 70.0
    except (TypeError, ValueError):
        threshold = 70.0
    if result["confidence"] < threshold:
        result["review_status"] = "needs_attention"
        result["risk_level"] = "review_required"

    doctor = _auto_assign_doctor(db)
    prediction = Prediction(
        patient_id=current_user.id,
        assigned_doctor_id=doctor.id if doctor else None,
        patient_name=patient_name or current_user.name,
        age=age if age is not None else current_user.age,
        gender=gender or current_user.gender,
        image_path=image_path,
        heatmap_path=result["heatmap_path"],
        predicted_class=result["predicted_class"],
        confidence=result["confidence"],
        status=result["status"],
        review_status=result["review_status"],
        risk_level=result["risk_level"],
        model_version=result["model_version"],
        explanation=result["explanation"],
    )
    db.add(prediction)
    db.flush()
    create_notification(
        db, current_user.id, "MRI report created",
        f"Report #{prediction.id} is {prediction.review_status.replace('_', ' ')} and waiting for doctor review.",
        prediction.id,
    )
    if doctor:
        create_notification(
            db, doctor.id, "New MRI review assigned",
            f"{prediction.patient_name}'s report #{prediction.id} requires review.",
            prediction.id,
        )
    add_audit_log(db, current_user, "prediction_created", "prediction", prediction.id)
    db.commit()
    db.refresh(prediction)

    response = serialize_prediction(prediction)
    response.update({"message": "Prediction completed successfully", "report_id": prediction.id, "mock_mode": result["mock_mode"]})
    return response


@router.get("/history")
def get_history(
    search: str | None = None,
    tumor_class: str | None = None,
    review_status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Prediction).options(joinedload(Prediction.assigned_doctor))
    if current_user.role == "patient":
        query = query.filter(Prediction.patient_id == current_user.id)
    elif current_user.role == "doctor":
        query = query.filter(Prediction.assigned_doctor_id == current_user.id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Prediction.patient_name.ilike(term), Prediction.predicted_class.ilike(term)))
    if tumor_class:
        query = query.filter(Prediction.predicted_class == tumor_class)
    if review_status:
        query = query.filter(Prediction.review_status == review_status)
    if date_from:
        try:
            query = query.filter(Prediction.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from must use YYYY-MM-DD format")
    if date_to:
        try:
            end = datetime.fromisoformat(date_to.replace("Z", ""))
            query = query.filter(Prediction.created_at <= end.replace(hour=23, minute=59, second=59))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to must use YYYY-MM-DD format")
    return [serialize_prediction(item) for item in query.order_by(Prediction.created_at.desc()).all()]


@router.get("/patient/dashboard")
def patient_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Patient access required")
    query = db.query(Prediction).filter(Prediction.patient_id == current_user.id)
    latest = query.order_by(Prediction.created_at.desc()).first()
    recent = query.order_by(Prediction.created_at.desc()).limit(5).all()
    unread = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).scalar()
    return {
        "total_reports": query.count(),
        "pending_reviews": query.filter(Prediction.review_status != "completed").count(),
        "completed_reviews": query.filter(Prediction.review_status == "completed").count(),
        "unread_notifications": unread or 0,
        "latest_prediction": serialize_prediction(latest) if latest else None,
        "recent_reports": [serialize_prediction(item) for item in recent],
    }


@router.get("/prediction/{report_id}")
def get_prediction_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = db.query(Prediction).options(joinedload(Prediction.assigned_doctor)).filter(Prediction.id == report_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction report not found")
    if not _can_access(prediction, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    return serialize_prediction(prediction)


@router.get("/prediction/{report_id}/image")
def view_mri_image(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prediction = db.query(Prediction).filter(Prediction.id == report_id).first()
    if not prediction or not _can_access(prediction, current_user):
        raise HTTPException(status_code=404, detail="MRI image not found")
    path = Path(prediction.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="MRI image file is missing")
    return FileResponse(path, media_type="image/png" if path.suffix.lower() == ".png" else "image/jpeg")


@router.get("/prediction/{report_id}/heatmap")
def view_heatmap(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prediction = db.query(Prediction).filter(Prediction.id == report_id).first()
    if not prediction or not _can_access(prediction, current_user) or not prediction.heatmap_path:
        raise HTTPException(status_code=404, detail="Grad-CAM heatmap is not available")
    path = Path(prediction.heatmap_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Grad-CAM heatmap file is missing")
    return FileResponse(path, media_type="image/png")


@router.get("/report/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prediction = db.query(Prediction).filter(Prediction.id == report_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction report not found")
    if not _can_access(prediction, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    report_path = generate_prediction_report(prediction)
    add_audit_log(db, current_user, "report_downloaded", "prediction", prediction.id)
    db.commit()
    return FileResponse(report_path, filename=f"brain_tumor_report_{report_id}.pdf", media_type="application/pdf")
