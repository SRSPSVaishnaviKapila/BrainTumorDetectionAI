def serialize_user(user) -> dict:
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
        "updated_at": user.updated_at,
    }


def serialize_prediction(prediction) -> dict:
    return {
        "id": prediction.id,
        "patient_id": prediction.patient_id,
        "assigned_doctor_id": prediction.assigned_doctor_id,
        "assigned_doctor_name": prediction.assigned_doctor.name if prediction.assigned_doctor else None,
        "patient_name": prediction.patient_name,
        "age": prediction.age,
        "gender": prediction.gender,
        "predicted_class": prediction.predicted_class,
        "confidence": prediction.confidence,
        "status": prediction.status,
        "review_status": prediction.review_status,
        "risk_level": prediction.risk_level,
        "doctor_remarks": prediction.doctor_remarks,
        "recommendation": prediction.recommendation,
        "follow_up_date": prediction.follow_up_date,
        "model_version": prediction.model_version,
        "explanation": prediction.explanation,
        "has_image": bool(prediction.image_path),
        "has_heatmap": bool(prediction.heatmap_path),
        "created_at": prediction.created_at,
        "updated_at": prediction.updated_at,
        "reviewed_at": prediction.reviewed_at,
    }
