from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.config import REPORTS_DIR


def generate_prediction_report(prediction) -> str:
    report_path = REPORTS_DIR / f"brain_tumor_report_{prediction.id}.pdf"
    c = canvas.Canvas(str(report_path), pagesize=A4)
    width, height = A4
    y = height - 45

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "Brain Tumor AI-Assisted Report")
    y -= 25
    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Decision-support report only. A qualified clinician must make the final diagnosis.")

    y = _section(c, y - 30, "Patient Details", [
        f"Report ID: {prediction.id}",
        f"Patient Name: {prediction.patient_name or 'N/A'}",
        f"Age: {prediction.age or 'N/A'}",
        f"Gender: {prediction.gender or 'N/A'}",
        f"Scan Date: {prediction.created_at.strftime('%d-%m-%Y %H:%M')}",
        f"Assigned Doctor: {prediction.assigned_doctor.name if prediction.assigned_doctor else 'Not assigned'}",
    ])

    y = _section(c, y - 10, "AI Prediction", [
        f"Predicted Class: {prediction.predicted_class}",
        f"Confidence: {prediction.confidence}%",
        f"AI Result: {prediction.status}",
        f"Risk Level: {prediction.risk_level}",
        f"Review Status: {prediction.review_status.replace('_', ' ').title()}",
        f"Model Version: {prediction.model_version or 'N/A'}",
    ])

    y = _wrapped_section(c, y - 10, "Explainable AI Summary", prediction.explanation or "No explanation is available.")
    y = _wrapped_section(c, y - 10, "Doctor Remarks", prediction.doctor_remarks or "No doctor remarks added yet.")
    y = _wrapped_section(c, y - 10, "Recommendation", prediction.recommendation or "No recommendation added yet.")
    c.setFont("Helvetica", 10)
    c.drawString(50, y - 5, f"Recommended Follow-up: {prediction.follow_up_date or 'Not specified'}")

    image_path = Path(prediction.image_path)
    heatmap_path = Path(prediction.heatmap_path) if prediction.heatmap_path else None
    image_y = 70
    if image_path.exists():
        try:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, image_y + 165, "Uploaded MRI")
            c.drawImage(str(image_path), 50, image_y, width=2.1 * inch, height=2.1 * inch, preserveAspectRatio=True)
        except Exception:
            pass
    if heatmap_path and heatmap_path.exists():
        try:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(310, image_y + 165, "Grad-CAM Visualization")
            c.drawImage(str(heatmap_path), 310, image_y, width=2.1 * inch, height=2.1 * inch, preserveAspectRatio=True)
        except Exception:
            pass

    c.setFont("Helvetica", 8)
    c.drawString(50, 30, "Disclaimer: AI output can be incorrect. Review the original MRI and clinical findings.")
    c.save()
    return str(report_path)


def _section(c, y: float, title: str, lines: list[str]) -> float:
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, title)
    y -= 18
    c.setFont("Helvetica", 10)
    for line in lines:
        c.drawString(55, y, line)
        y -= 15
    return y


def _wrapped_section(c, y: float, title: str, text: str) -> float:
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, title)
    y -= 18
    body = c.beginText(55, y)
    body.setFont("Helvetica", 10)
    lines = split_text(text, 90)
    for line in lines[:5]:
        body.textLine(line)
        y -= 13
    c.drawText(body)
    return y


def split_text(text: str, max_chars: int):
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += (" " if current else "") + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
