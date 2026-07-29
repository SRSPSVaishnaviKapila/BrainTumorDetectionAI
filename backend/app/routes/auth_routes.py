from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db, User, Notification, SystemSetting, add_audit_log
from app.utils.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    phone: str | None = None


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "age": user.age,
        "gender": user.gender,
        "phone": user.phone,
        "specialization": user.specialization,
        "registration_number": user.registration_number,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.post("/register", status_code=201)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Public registration intentionally creates patient accounts only."""
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=get_password_hash(payload.password),
        role="patient",
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        is_active=True,
    )
    db.add(user)
    db.flush()
    add_audit_log(db, user, "patient_registered", "user", user.id)
    db.commit()
    db.refresh(user)
    return {"message": "Patient account created successfully", "user": serialize_user(user)}


@router.post("/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account is inactive. Contact the administrator.")
    maintenance = db.query(SystemSetting).filter(SystemSetting.key == "maintenance_mode").first()
    if maintenance and maintenance.value == "true" and user.role != "admin":
        raise HTTPException(status_code=503, detail="The system is temporarily in maintenance mode")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    add_audit_log(db, user, "login", "user", user.id)
    db.commit()
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


@router.put("/profile")
def update_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value.strip() if isinstance(value, str) else value)
    add_audit_log(db, current_user, "profile_updated", "user", current_user.id)
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully", "user": serialize_user(current_user)}


@router.put("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different")

    current_user.password_hash = get_password_hash(payload.new_password)
    add_audit_log(db, current_user, "password_changed", "user", current_user.id)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/notifications")
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).limit(50).all()


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.put("/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read"}
