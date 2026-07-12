from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ready",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": settings.app_version,
    }
