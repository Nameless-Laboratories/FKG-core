"""FastAPI application setup."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fkg.api.routes import edges, entities, health, pkg, provenance, whoami
from fkg.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="FKG-Core API",
        description="County-hosted knowledge graph runtime API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS if enabled
    if settings.api.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.api.cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["GET"],  # Read-only API
            allow_headers=["*"],
        )

    # Register routes
    app.include_router(health.router, tags=["Health"])
    app.include_router(whoami.router, tags=["Identity"])
    app.include_router(entities.router, prefix="/entities", tags=["Entities"])
    app.include_router(edges.router, prefix="/edges", tags=["Edges"])
    app.include_router(provenance.router, tags=["Provenance"])
    app.include_router(pkg.router, prefix="/pkg", tags=["PKG"])

    return app


app = create_app()
