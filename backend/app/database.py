from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    ForeignKey, Text, Boolean, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from .config import DATABASE_URL, create_required_dirs

create_required_dirs()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="patient", index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(30), nullable=True)
    phone = Column(String(30), nullable=True)
    specialization = Column(String(120), nullable=True)
    registration_number = Column(String(80), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    predictions = relationship(
        "Prediction", back_populates="patient", foreign_keys="Prediction.patient_id"
    )
    assigned_reports = relationship(
        "Prediction", back_populates="assigned_doctor", foreign_keys="Prediction.assigned_doctor_id"
    )
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    patient_name = Column(String(120), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(30), nullable=True)

    image_path = Column(String(500), nullable=False)
    heatmap_path = Column(String(500), nullable=True)
    predicted_class = Column(String(80), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    status = Column(String(80), nullable=False)  # AI result: Tumor/No Tumor
    review_status = Column(String(40), default="pending_review", nullable=False, index=True)
    risk_level = Column(String(30), default="normal", nullable=False, index=True)

    doctor_remarks = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    follow_up_date = Column(String(30), nullable=True)
    model_version = Column(String(80), nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    patient = relationship("User", back_populates="predictions", foreign_keys=[patient_id])
    assigned_doctor = relationship("User", back_populates="assigned_reports", foreign_keys=[assigned_doctor_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    report_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True, index=True)
    actor_email = Column(String(160), nullable=True)
    action = Column(String(120), nullable=False, index=True)
    entity_type = Column(String(80), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(120), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def _migrate_sqlite_columns() -> None:
    """Adds newly introduced columns when an older SQLite DB is reused."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    migrations = {
        "users": {
            "phone": "VARCHAR(30)",
            "specialization": "VARCHAR(120)",
            "registration_number": "VARCHAR(80)",
            "is_active": "BOOLEAN NOT NULL DEFAULT 1",
            "updated_at": "DATETIME",
        },
        "predictions": {
            "assigned_doctor_id": "INTEGER",
            "heatmap_path": "VARCHAR(500)",
            "review_status": "VARCHAR(40) NOT NULL DEFAULT 'pending_review'",
            "risk_level": "VARCHAR(30) NOT NULL DEFAULT 'normal'",
            "recommendation": "TEXT",
            "follow_up_date": "VARCHAR(30)",
            "model_version": "VARCHAR(80)",
            "explanation": "TEXT",
            "updated_at": "DATETIME",
            "reviewed_at": "DATETIME",
        },
    }

    with engine.begin() as connection:
        for table, columns in migrations.items():
            existing = {
                row[1] for row in connection.execute(text(f"PRAGMA table_info({table})")).fetchall()
            }
            for column, sql_type in columns.items():
                if column not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))


def init_db() -> None:
    create_required_dirs()
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_columns()
    seed_demo_users()


def seed_demo_users() -> None:
    from .utils.security import get_password_hash

    db = SessionLocal()
    try:
        demo_users = [
            dict(name="Admin", email="admin@gmail.com", password="admin123", role="admin"),
            dict(
                name="Dr. Ravi", email="doctor@gmail.com", password="doctor123", role="doctor",
                specialization="Radiology", registration_number="DEMO-RAD-001"
            ),
            dict(
                name="Sai Kumar", email="patient@gmail.com", password="patient123", role="patient",
                age=22, gender="Male"
            ),
        ]
        for data in demo_users:
            if not db.query(User).filter(User.email == data["email"]).first():
                password = data.pop("password")
                db.add(User(password_hash=get_password_hash(password), **data))
        defaults = {
            "system_name": "Brain Tumor AI",
            "maintenance_mode": "false",
            "confidence_threshold": "70",
        }
        for key, value in defaults.items():
            if not db.query(SystemSetting).filter(SystemSetting.key == key).first():
                db.add(SystemSetting(key=key, value=value))
        db.commit()
    finally:
        db.close()


def add_audit_log(db, actor, action: str, entity_type: str | None = None,
                  entity_id: int | None = None, details: str | None = None) -> None:
    db.add(AuditLog(
        actor_id=getattr(actor, "id", None),
        actor_email=getattr(actor, "email", None),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    ))


def create_notification(db, user_id: int | None, title: str, message: str,
                        report_id: int | None = None) -> None:
    if user_id:
        db.add(Notification(
            user_id=user_id, title=title, message=message, report_id=report_id
        ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
