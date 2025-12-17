"""Health check endpoint."""

from fastapi import APIRouter

from fkg.db import check_database_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check API and database health."""
    db_ok = check_database_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }
