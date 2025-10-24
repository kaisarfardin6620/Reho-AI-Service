from fastapi import APIRouter

router = APIRouter(
    tags=["Health Check"] 
)

@router.get("/health")
def health_check():
    return {"status": "ok", "message": "AI service is healthy"}