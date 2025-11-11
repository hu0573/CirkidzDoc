from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="健康检查", tags=["health"])
def health_check() -> dict[str, str]:
    """
    返回服务健康状态与关键信息。
    """

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "version": settings.app_version,
    }

