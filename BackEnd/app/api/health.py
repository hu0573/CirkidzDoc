from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from fastapi import APIRouter

from app.core.config import settings
from app.services.dependency_check import collect_dependency_status

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    environment: str
    version: str
    dependencies: dict[str, bool]


@router.get("/health", summary="Health check", tags=["health"])
def health_check() -> HealthResponse:
    """
    Return the service health status along with key information.
    """

    dependencies = {
        status.name: status.available
        for status in collect_dependency_status()
    }

    degraded = not all(dependencies.values())

    return HealthResponse(
        status="degraded" if degraded else "ok",
        environment=settings.environment,
        version=settings.app_version,
        dependencies=dependencies,
    )

