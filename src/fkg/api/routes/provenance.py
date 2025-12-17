"""Provenance API endpoints."""

from fastapi import APIRouter, HTTPException

from fkg.db import get_sync_session
from fkg.storage.entities import EntityStorage
from fkg.storage.sources import SourceStorage

router = APIRouter()


@router.get("/entities/{entity_id}/provenance")
async def get_entity_provenance(entity_id: str):
    """Get provenance information for an entity."""
    session = get_sync_session()
    try:
        entity_storage = EntityStorage(session)
        source_storage = SourceStorage(session)

        # Check entity exists
        entity = entity_storage.get(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Get provenance info
        provenance = source_storage.get_entity_provenance(entity_id)

        return provenance
    finally:
        session.close()


@router.get("/sources/{source_id}")
async def get_source(source_id: str):
    """Get a source by ID."""
    session = get_sync_session()
    try:
        storage = SourceStorage(session)
        source = storage.get_source(source_id)

        if source is None:
            raise HTTPException(status_code=404, detail="Source not found")

        return source.to_dict()
    finally:
        session.close()
