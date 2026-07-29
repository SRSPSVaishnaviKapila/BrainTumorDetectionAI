# Implemented Features

## Patient
- Secure patient-only registration and role-protected login
- Profile viewing/updating and password change
- JPG/PNG/DICOM MRI upload with validation
- AI result, confidence, risk, explanation, model version, and optional Grad-CAM
- Search/filter prediction history and scan timeline
- Assigned-doctor, review-status, remarks, recommendation, and follow-up display
- In-app status notifications
- Authenticated PDF download and print view

## Doctor
- Assigned-patient and assigned-report workflow
- Dashboard totals for patients, reports, pending/completed reviews, and high-risk cases
- Patient/report search and filtering
- MRI and optional Grad-CAM viewing
- Patient profile summary and historical report comparison
- Add/edit remarks, recommendations, follow-up dates, and review status
- PDF download and browser printing

## Admin
- System statistics, class analytics, daily/monthly activity, model status, health, and storage usage
- User search/filter/edit, activate/deactivate, and doctor create/edit/delete
- Prediction filtering and doctor reassignment
- CSV prediction export and PDF system summary export
- Audit logs and system settings
- SQLite database backup and validated restore

## Security and workflow
- Public registration cannot create doctor/admin accounts
- Frontend and backend role guards
- Inactive-account enforcement
- Maintenance-mode enforcement
- Environment-based JWT/model configuration
- Automatic doctor assignment, low-confidence flagging, notifications, and audit records

A trained model and evaluation dataset are not included. Actual clinical predictions and accuracy/precision/recall/F1/confusion-matrix values require those project assets.
