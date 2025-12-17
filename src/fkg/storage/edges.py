"""Storage operations for edges."""

from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from fkg.changelog.append import append_event
from fkg.ids.make_id import make_edge_id
from fkg.models.edge import Edge
from fkg.settings import get_settings
from fkg.validate import validate_edge


class EdgeStorage:
    """Storage operations for edges."""

    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session

    def get(self, edge_id: str) -> Edge | None:
        """Get an edge by ID.

        Args:
            edge_id: The edge ID

        Returns:
            The edge or None if not found
        """
        return self.session.get(Edge, edge_id)

    def list(
        self,
        edge_type: str | None = None,
        src_id: str | None = None,
        dst_id: str | None = None,
        authority_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Edge]:
        """List edges with optional filtering.

        Args:
            edge_type: Filter by edge type
            src_id: Filter by source entity
            dst_id: Filter by destination entity
            authority_id: Filter by authority
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            List of matching edges
        """
        stmt = select(Edge)

        if edge_type:
            stmt = stmt.where(Edge.type == edge_type)

        if src_id:
            stmt = stmt.where(Edge.src_id == src_id)

        if dst_id:
            stmt = stmt.where(Edge.dst_id == dst_id)

        if authority_id:
            stmt = stmt.where(Edge.authority_id == authority_id)

        stmt = stmt.order_by(Edge.created_at.desc()).limit(limit).offset(offset)

        return list(self.session.execute(stmt).scalars().all())

    def count(
        self,
        edge_type: str | None = None,
        authority_id: str | None = None,
    ) -> int:
        """Count edges with optional filtering.

        Args:
            edge_type: Filter by edge type
            authority_id: Filter by authority

        Returns:
            Count of matching edges
        """
        stmt = select(func.count()).select_from(Edge)

        if edge_type:
            stmt = stmt.where(Edge.type == edge_type)

        if authority_id:
            stmt = stmt.where(Edge.authority_id == authority_id)

        return self.session.execute(stmt).scalar() or 0

    def upsert(
        self,
        data: dict[str, Any],
        authority_id: str | None = None,
        schema_version: str = "v0.1",
        validate: bool = True,
        log_event: bool = True,
    ) -> Edge:
        """Insert or update an edge.

        Args:
            data: Edge data (must include type, src_id, dst_id)
            authority_id: Authority ID (uses settings if not provided)
            schema_version: Schema version
            validate: Whether to validate against schema
            log_event: Whether to log a changelog event

        Returns:
            The created/updated edge
        """
        # Validate required fields
        edge_type = data.get("type")
        src_id = data.get("src_id")
        dst_id = data.get("dst_id")

        if not all([edge_type, src_id, dst_id]):
            raise ValueError("Edge must have type, src_id, and dst_id")

        # Determine authority
        if authority_id is None:
            settings = get_settings()
            authority_id = settings.instance.id

        # Validate if requested
        if validate:
            validate_edge(data, schema_version)

        # Generate ID if not provided
        edge_id = data.get("id")
        properties = data.get("properties", {})

        if edge_id is None:
            edge_id = make_edge_id(authority_id, edge_type, src_id, dst_id, properties)

        # Check for existing edge
        existing = self.get(edge_id)

        # Prepare edge data
        edge_data = {
            "properties": properties,
        }
        # Include any extra fields
        for k, v in data.items():
            if k not in ("id", "type", "src_id", "dst_id", "schema_version", "authority_id", "properties"):
                edge_data[k] = v

        if existing:
            # Update existing edge
            existing.data = edge_data
            existing.schema_version = schema_version
            edge = existing
            event_type = "update_edge"
        else:
            # Create new edge
            edge = Edge(
                id=edge_id,
                type=edge_type,
                src_id=src_id,
                dst_id=dst_id,
                schema_version=schema_version,
                authority_id=authority_id,
                data=edge_data,
            )
            self.session.add(edge)
            event_type = "create_edge"

        # Log event
        if log_event:
            append_event(
                self.session,
                event_type=event_type,
                authority_id=authority_id,
                payload={
                    "edge_id": edge_id,
                    "type": edge_type,
                    "src_id": src_id,
                    "dst_id": dst_id,
                },
            )

        self.session.flush()
        return edge

    def delete(self, edge_id: str, log_event: bool = True) -> bool:
        """Delete an edge.

        Args:
            edge_id: The edge ID to delete
            log_event: Whether to log a changelog event

        Returns:
            True if edge was deleted, False if not found
        """
        edge = self.get(edge_id)
        if edge is None:
            return False

        authority_id = edge.authority_id
        edge_type = edge.type

        self.session.delete(edge)

        if log_event:
            append_event(
                self.session,
                event_type="delete_edge",
                authority_id=authority_id,
                payload={"edge_id": edge_id, "type": edge_type},
            )

        self.session.flush()
        return True

    def get_by_endpoints(
        self,
        src_id: str,
        dst_id: str,
        edge_type: str | None = None,
    ) -> list[Edge]:
        """Get edges between two entities.

        Args:
            src_id: Source entity ID
            dst_id: Destination entity ID
            edge_type: Optional edge type filter

        Returns:
            List of edges between the entities
        """
        stmt = select(Edge).where(Edge.src_id == src_id, Edge.dst_id == dst_id)

        if edge_type:
            stmt = stmt.where(Edge.type == edge_type)

        return list(self.session.execute(stmt).scalars().all())
