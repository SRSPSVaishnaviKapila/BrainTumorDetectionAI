# NeuroScan AI – Brain Tumor Detection and Doctor Review System

Full-stack React + FastAPI project for AI-assisted brain MRI classification and clinical review workflow.

## Implemented workflow

1. Patient registers, logs in, manages profile/password, and uploads JPG/PNG/DICOM MRI scans.
2. The AI module classifies the scan, records confidence/risk/model version, and generates an explainable summary.
3. Low-confidence results are flagged and each report is automatically assigned to an active doctor.
4. The doctor views the MRI, searches assigned patients, compares previous reports, adds remarks/recommendations/follow-up, and completes the review.
5. The patient receives in-app report status notifications and can view, print, search, and download the final PDF report.
6. Admin manages doctors/users, activation status, assignments, filters, statistics, CSV/PDF exports, settings, audit logs, database backup, and restore.

Grad-CAM is generated automatically when a compatible trained Keras model is available. If no model file is present, the application runs in clearly labelled deterministic demo mode; demo outputs are not medical predictions.

## Run backend

Use Python 3.11 because the pinned TensorFlow version is intended for that Python version.

```bash
cd backend
py -3.11 -m venv ../venv
..\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

API documentation: `http://127.0.0.1:8000/docs`

Place the trained model at:

```text
backend/model/brain_tumor_model.keras
```

The backend reads environment variables directly. On Windows PowerShell, load them before starting or use your preferred dotenv runner.

## Run frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend: `http://localhost:5173`

## Local demonstration accounts

These are seeded only for local project demonstration. Change or remove them before deployment.

```text
Patient: patient@gmail.com / patient123
Doctor:  doctor@gmail.com / doctor123
Admin:   admin@gmail.com / admin123
```

## Important limitations

- A trained model is not included in this ZIP.
- Accuracy, precision, recall, F1-score, and confusion matrix must come from your actual held-out evaluation dataset. The project does not invent those metrics.
- The system is an educational decision-support project and not a certified medical device.
- Set a strong `JWT_SECRET_KEY`, remove demo accounts, use HTTPS, and use a production database before deployment.
