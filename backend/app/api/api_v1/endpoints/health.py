from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "Acture Advisor 2.0 Backend"}
