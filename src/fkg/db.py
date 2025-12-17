"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from fkg.settings import get_settings


def get_sync_engine():
    """Get a synchronous database engine."""
    settings = get_settings()
    # Convert async URL to sync URL if needed
    url = settings.database.url
    if "+psycopg" in url and "async" not in url:
        sync_url = url
    else:
        sync_url = url.replace("postgresql+asyncpg", "postgresql+psycopg")
    return create_engine(sync_url, echo=False)


def get_async_engine():
    """Get an async database engine."""
    settings = get_settings()
    url = settings.database.url
    # Convert to asyncpg if using psycopg
    async_url = url.replace("postgresql+psycopg", "postgresql+asyncpg")
    return create_async_engine(async_url, echo=False)


def get_sync_session() -> Session:
    """Get a synchronous database session."""
    engine = get_sync_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


async def get_async_session() -> AsyncSession:
    """Get an async database session."""
    engine = get_async_engine()
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    return AsyncSessionLocal()


@asynccontextmanager
async def async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions."""
    session = await get_async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def check_database_connection() -> bool:
    """Check if the database connection works."""
    try:
        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_database() -> None:
    """Initialize the database schema using Alembic."""
    from alembic import command
    from alembic.config import Config

    from fkg.settings import get_settings

    settings = get_settings()

    # Find alembic.ini
    from pathlib import Path

    alembic_ini = Path(__file__).parent.parent.parent.parent / "alembic.ini"
    if not alembic_ini.exists():
        alembic_ini = Path.cwd() / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)

    command.upgrade(alembic_cfg, "head")
