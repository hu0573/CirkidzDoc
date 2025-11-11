from fastapi import APIRouter

from app.api import formats, health, templates

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(templates.router, prefix="/api/templates", tags=["templates"])
api_router.include_router(formats.router, prefix="/api/formats", tags=["formats"])

