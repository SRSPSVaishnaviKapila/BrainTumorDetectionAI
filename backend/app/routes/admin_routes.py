import csv
import io
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.config import DATABASE_PATH, BACKUP_DIR, UPLOAD_DIR, HEATMAP_DIR, REPORTS_DIR
from app.database import (
    get_db, User, Prediction, AuditLog, SystemSetting,
    add_audit_log, create_notification
)
from app.services.ml_service import ml_service
from app.utils.security import require_role, get_password_hash
from app.utils.serializers import serialize_user, serialize_prediction

router = APIRouter(prefix="/admin", tags=["Admin"])


class DoctorCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    phone: str | None = None
    specialization: str | None = None
    registration_number: str | None = None


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    phone: str | None = None
    specialization: str | None = None
    registration_number: str | None = None


class ActiveRequest(BaseModel):
    is_active: bool


class AssignDoctorRequest(BaseModel):
    doctor_id: int


class SettingsRequest(BaseModel):
    system_name: str | None = None
    maintenance_mode: bool | None = None
    confidence_threshold: float | None = Field(default=None, ge=1, le=100)


def _directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    total_users = db.query(User).count()
    total_patients = db.query(User).filter(User.role == "patient").count()
    total_doctors = db.query(User).filter(User.role == "doctor").count()
    total_predictions = db.query(Prediction).count()
    class_counts = {key: 0 for key in ["glioma", "meningioma", "notumor", "pituitary"]}
    for class_name, count in db.query(Prediction.predicted_class, func.count(Prediction.id)).group_by(Prediction.predicted_class).all():
        class_counts[class_name] = count

    start = datetime.utcnow() - timedelta(days=29)
    daily_rows = db.query(
        func.date(Prediction.created_at), func.count(Prediction.id)
    ).filter(Prediction.created_at >= start).group_by(func.date(Prediction.created_at)).all()
    monthly_rows = db.query(
        func.strftime("%Y-%m", Prediction.created_at), func.count(Prediction.id)
    ).group_by(func.strftime("%Y-%m", Prediction.created_at)).order_by(
        func.strftime("%Y-%m", Prediction.created_at).desc()
    ).limit(12).all()

    return {
        "total_users": total_users,
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
        "inactive_users": db.query(User).filter(User.is_active.is_(False)).count(),
        "total_mri_scans": total_predictions,
        "total_predictions": total_predictions,
        "pending_reviews": db.query(Prediction).filter(Prediction.review_status != "completed").count(),
        "completed_reviews": db.query(Prediction).filter(Prediction.review_status == "completed").count(),
        "class_counts": class_counts,
        "daily_predictions": [{"date": str(day), "count": count} for day, count in daily_rows],
        "monthly_predictions": [{"month": str(month), "count": count} for month, count in reversed(monthly_rows)],
        "model": ml_service.info(),
        "system_health": "healthy",
        "storage_usage_bytes": _directory_size(UPLOAD_DIR) + _directory_size(HEATMAP_DIR) + _directory_size(REPORTS_DIR),
    }


@router.get("/users")
def list_users(
    search: str | None = None,
    role: str | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    query = db.query(User)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.name.ilike(term), User.email.ilike(term)))
    if role:
        query = query.filter(User.role == role)
    if active is not None:
        query = query.filter(User.is_active == active)
    return [serialize_user(user) for user in query.order_by(User.created_at.desc()).all()]


@router.post("/doctors", status_code=201)
def add_doctor(payload: DoctorCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    doctor = User(
        name=payload.name.strip(), email=payload.email.lower(),
        password_hash=get_password_hash(payload.password), role="doctor",
        phone=payload.phone, specialization=payload.specialization,
        registration_number=payload.registration_number, is_active=True,
    )
    db.add(doctor)
    db.flush()
    add_audit_log(db, current_user, "doctor_created", "user", doctor.id)
    db.commit()
    db.refresh(doctor)
    return {"message": "Doctor created successfully", "doctor": serialize_user(doctor)}


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value.strip() if isinstance(value, str) else value)
    add_audit_log(db, current_user, "user_updated", "user", user.id)
    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully", "user": serialize_user(user)}


@router.put("/users/{user_id}/active")
def set_user_active(user_id: int, payload: ActiveRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id and not payload.is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account")
    user.is_active = payload.is_active
    add_audit_log(db, current_user, "user_activated" if payload.is_active else "user_deactivated", "user", user.id)
    db.commit()
    return {"message": "User status updated successfully"}


@router.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    doctor = db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    assigned = db.query(Prediction).filter(Prediction.assigned_doctor_id == doctor.id).count()
    if assigned:
        raise HTTPException(status_code=409, detail="Doctor has assigned reports. Reassign them before deletion.")
    add_audit_log(db, current_user, "doctor_deleted", "user", doctor.id)
    db.delete(doctor)
    db.commit()
    return {"message": "Doctor deleted successfully"}


@router.get("/predictions")
def list_predictions(
    search: str | None = None,
    tumor_class: str | None = None,
    review_status: str | None = None,
    doctor_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    query = db.query(Prediction).options(joinedload(Prediction.assigned_doctor))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Prediction.patient_name.ilike(term), Prediction.predicted_class.ilike(term)))
    if tumor_class:
        query = query.filter(Prediction.predicted_class == tumor_class)
    if review_status:
        query = query.filter(Prediction.review_status == review_status)
    if doctor_id:
        query = query.filter(Prediction.assigned_doctor_id == doctor_id)
    return [serialize_prediction(item) for item in query.order_by(Prediction.created_at.desc()).all()]


@router.put("/predictions/{report_id}/assign")
def assign_doctor(report_id: int, payload: AssignDoctorRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    report = db.query(Prediction).filter(Prediction.id == report_id).first()
    doctor = db.query(User).filter(User.id == payload.doctor_id, User.role == "doctor", User.is_active.is_(True)).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not doctor:
        raise HTTPException(status_code=404, detail="Active doctor not found")
    report.assigned_doctor_id = doctor.id
    create_notification(db, doctor.id, "MRI review assigned", f"Report #{report.id} for {report.patient_name} was assigned to you.", report.id)
    add_audit_log(db, current_user, "report_assigned", "prediction", report.id, f"doctor_id={doctor.id}")
    db.commit()
    return {"message": "Doctor assigned successfully"}


@router.get("/audit-logs")
def audit_logs(limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    limit = max(1, min(limit, 500))
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    return {item.key: item.value for item in db.query(SystemSetting).all()}


@router.put("/settings")
def update_settings(payload: SettingsRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        text_value = str(value).lower() if isinstance(value, bool) else str(value)
        if setting:
            setting.value = text_value
        else:
            db.add(SystemSetting(key=key, value=text_value))
    add_audit_log(db, current_user, "system_settings_updated", "settings")
    db.commit()
    return {"message": "System settings updated successfully"}


@router.get("/export/predictions.csv")
def export_predictions_csv(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Report ID", "Patient", "Tumor Class", "Confidence", "AI Status", "Review Status", "Risk", "Doctor", "Created At"])
    reports = db.query(Prediction).options(joinedload(Prediction.assigned_doctor)).order_by(Prediction.created_at.desc()).all()
    for item in reports:
        writer.writerow([item.id, item.patient_name, item.predicted_class, item.confidence, item.status, item.review_status, item.risk_level, item.assigned_doctor.name if item.assigned_doctor else "", item.created_at.isoformat()])
    add_audit_log(db, current_user, "predictions_exported_csv", "prediction")
    db.commit()
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=prediction_reports.csv"})


@router.get("/export/summary.pdf")
def export_summary_pdf(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    path = REPORTS_DIR / f"admin_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "Brain Tumor AI - System Summary")
    c.setFont("Helvetica", 11)
    rows = [
        ("Generated", datetime.utcnow().strftime("%d-%m-%Y %H:%M UTC")),
        ("Total users", db.query(User).count()),
        ("Doctors", db.query(User).filter(User.role == "doctor").count()),
        ("Patients", db.query(User).filter(User.role == "patient").count()),
        ("Predictions", db.query(Prediction).count()),
        ("Pending reviews", db.query(Prediction).filter(Prediction.review_status != "completed").count()),
        ("Completed reviews", db.query(Prediction).filter(Prediction.review_status == "completed").count()),
        ("Model loaded", "Yes" if not ml_service.mock_mode else "No - demo mode"),
    ]
    y = 755
    for label, value in rows:
        c.drawString(60, y, f"{label}: {value}")
        y -= 26
    c.save()
    add_audit_log(db, current_user, "summary_exported_pdf", "system")
    db.commit()
    return FileResponse(path, filename="brain_tumor_system_summary.pdf", media_type="application/pdf")


@router.get("/backup")
def backup_database(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    backup_path = BACKUP_DIR / f"brain_tumor_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    db.commit()
    shutil.copy2(DATABASE_PATH, backup_path)
    add_audit_log(db, current_user, "database_backup_created", "database")
    db.commit()
    return FileResponse(backup_path, filename=backup_path.name, media_type="application/octet-stream")


@router.post("/restore")
async def restore_database(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    contents = await file.read()
    if not contents.startswith(b"SQLite format 3"):
        raise HTTPException(status_code=400, detail="Only a valid SQLite database backup is accepted")
    temp_path = BACKUP_DIR / "restore_candidate.db"
    temp_path.write_bytes(contents)
    try:
        connection = sqlite3.connect(temp_path)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        connection.close()
        if not {"users", "predictions"}.issubset(tables):
            raise HTTPException(status_code=400, detail="Backup does not contain the required application tables")
        safety = BACKUP_DIR / f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DATABASE_PATH, safety)
        shutil.copy2(temp_path, DATABASE_PATH)
    finally:
        temp_path.unlink(missing_ok=True)
    return {"message": "Database restored. Restart the backend before using the application."}
