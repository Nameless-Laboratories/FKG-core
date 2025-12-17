"""Edge API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from fkg.db import get_sync_session
from fkg.storage.edges import EdgeStorage

router = APIRouter()


@router.get("")
async def list_edges(
    type: str | None = Query(None, description="Filter by edge type"),
    src_id: str | None = Query(None, description="Filter by source entity"),
    dst_id: str | None = Query(None, description="Filter by destination entity"),
    authority_id: str | None = Query(None, description="Filter by authority"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List edges with optional filtering."""
    session = get_sync_session()
    try:
        storage = EdgeStorage(session)
        edges = storage.list(
            edge_type=type,
            src_id=src_id,
            dst_id=dst_id,
            authority_id=authority_id,
            limit=limit,
            offset=offset,
        )
        total = storage.count(edge_type=type, authority_id=authority_id)

        return {
            "items": [e.to_dict() for e in edges],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        session.close()


@router.get("/{edge_id}")
async def get_edge(edge_id: str):
    """Get an edge by ID."""
    session = get_sync_session()
    try:
        storage = EdgeStorage(session)
        edge = storage.get(edge_id)

        if edge is None:
            raise HTTPException(status_code=404, detail="Edge not found")

        return edge.to_dict()
    finally:
        session.close()
