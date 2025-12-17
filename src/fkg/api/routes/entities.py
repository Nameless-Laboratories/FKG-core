"""Entity API endpoints."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from fkg.db import get_sync_session
from fkg.storage.entities import EntityStorage

router = APIRouter()


@router.get("")
async def list_entities(
    type: str | None = Query(None, description="Filter by entity type"),
    query: str | None = Query(None, description="Search query (matches name)"),
    authority_id: str | None = Query(None, description="Filter by authority"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List entities with optional filtering."""
    session = get_sync_session()
    try:
        storage = EntityStorage(session)
        entities = storage.list(
            entity_type=type,
            authority_id=authority_id,
            query=query,
            limit=limit,
            offset=offset,
        )
        total = storage.count(entity_type=type, authority_id=authority_id)

        return {
            "items": [e.to_dict() for e in entities],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        session.close()


@router.get("/{entity_id}")
async def get_entity(entity_id: str):
    """Get an entity by ID."""
    session = get_sync_session()
    try:
        storage = EntityStorage(session)
        entity = storage.get(entity_id)

        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")

        return entity.to_dict()
    finally:
        session.close()


@router.get("/{entity_id}/neighbors")
async def get_neighbors(
    entity_id: str,
    edge_type: str | None = Query(None, description="Filter by edge type"),
    direction: Literal["out", "in"] = Query("out", description="Edge direction"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
):
    """Get neighboring entities connected by edges."""
    session = get_sync_session()
    try:
        storage = EntityStorage(session)

        # Check entity exists
        entity = storage.get(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")

        neighbors = storage.get_neighbors(
            entity_id,
            edge_type=edge_type,
            direction=direction,
            limit=limit,
        )

        return {
            "entity_id": entity_id,
            "direction": direction,
            "edge_type": edge_type,
            "neighbors": [n.to_dict() for n in neighbors],
        }
    finally:
        session.close()
