"""Instance identity endpoint."""

from fastapi import APIRouter

from fkg.settings import get_settings
from fkg.validate.registry import get_registry

router = APIRouter()


@router.get("/whoami")
async def whoami():
    """Get instance identity information."""
    settings = get_settings()
    registry = get_registry()

    return {
        "instance_id": settings.instance.id,
        "authority_name": settings.instance.authority_name,
        "jurisdiction": settings.instance.jurisdiction,
        "public_key": settings.instance.public_key,
        "schema_version": settings.instance.schema_version,
        "available_schema_versions": registry.list_versions(),
        "available_entity_types": registry.list_entity_types(settings.instance.schema_version),
    }
