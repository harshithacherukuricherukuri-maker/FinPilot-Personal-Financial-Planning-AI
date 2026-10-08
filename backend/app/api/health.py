from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """Return platform operational health status."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }
