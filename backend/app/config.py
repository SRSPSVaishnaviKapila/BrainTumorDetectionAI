import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "brain_tumor.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")

MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = Path(os.getenv("MODEL_PATH", MODEL_DIR / "brain_tumor_model.keras"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "unversioned")
MODEL_ACCURACY = os.getenv("MODEL_ACCURACY")

REPORTS_DIR = BASE_DIR / "reports"
UPLOAD_DIR = APP_DIR / "uploads" / "mri_images"
HEATMAP_DIR = APP_DIR / "uploads" / "heatmaps"
BACKUP_DIR = BASE_DIR / "backups"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "application/dicom", "application/octet-stream"
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".dcm"}
CLASS_NAMES = ["glioma", "meningioma", "notumor", "pituitary"]
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "70"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-this-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))


def create_required_dirs() -> None:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    HEATMAP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
