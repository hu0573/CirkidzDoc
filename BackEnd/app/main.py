from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_database


def create_app() -> FastAPI:
    """
    Application factory that initializes logging, the FastAPI instance, and registers routers.
    """

    configure_logging()
    init_database()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS: allow all origins if enabled or in development, otherwise use specific origins
    cors_kwargs = {
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if settings.cors_allow_all_origins or settings.environment == "development":
        cors_kwargs["allow_origins"] = ["*"]
    else:
        cors_kwargs["allow_origins"] = list(settings.cors_allow_origins)

    application.add_middleware(
        CORSMiddleware,
        **cors_kwargs,
    )

    application.include_router(api_router)

    return application


app = create_app()

