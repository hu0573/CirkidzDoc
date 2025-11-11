from fastapi import APIRouter

from app.api import health, templates

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(templates.router, prefix="/api/templates", tags=["templates"])

