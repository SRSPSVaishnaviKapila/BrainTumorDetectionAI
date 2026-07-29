from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/health")
def report_health():
    return {"status": "Report service is running"}
