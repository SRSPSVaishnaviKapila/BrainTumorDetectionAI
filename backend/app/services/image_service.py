from pathlib import Path
from uuid import uuid4
import io

import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile, HTTPException

from app.config import UPLOAD_DIR, ALLOWED_IMAGE_TYPES, ALLOWED_EXTENSIONS


async def save_uploaded_image(file: UploadFile) -> str:
    original_name = file.filename or "scan"
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, PNG, and DICOM (.dcm) MRI files are allowed")
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES and extension != ".dcm":
        raise HTTPException(status_code=400, detail="Unsupported MRI file type")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="MRI file must be smaller than 20 MB")

    try:
        if extension == ".dcm":
            image = _dicom_to_image(contents)
            extension = ".png"
        else:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            image.verify()
            image = Image.open(io.BytesIO(contents)).convert("RGB")
    except (UnidentifiedImageError, ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"The uploaded file is not a readable medical image: {exc}")

    if image.width < 64 or image.height < 64:
        raise HTTPException(status_code=400, detail="MRI image resolution is too small")

    filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    image.save(file_path, format="PNG" if extension == ".png" else "JPEG", quality=95)
    return str(file_path)


def _dicom_to_image(contents: bytes) -> Image.Image:
    try:
        import pydicom
    except ImportError as exc:
        raise ValueError("DICOM support requires the pydicom package") from exc

    dataset = pydicom.dcmread(io.BytesIO(contents), force=True)
    pixels = dataset.pixel_array.astype("float32")
    pixels -= pixels.min()
    maximum = pixels.max()
    if maximum > 0:
        pixels /= maximum
    pixels = (pixels * 255).clip(0, 255).astype("uint8")
    if pixels.ndim > 2:
        pixels = pixels[0]
    return Image.fromarray(pixels).convert("RGB")
