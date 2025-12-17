"""Storage operations for entities."""

from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from fkg.changelog.append import append_event
from fkg.ids import make_id
from fkg.models.entity import Entity
from fkg.settings import get_settings
from fkg.validate import validate_entity


class EntityStorage:
    """Storage operations for entities."""

    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session

    def get(self, entity_id: str) -> Entity | None:
        """Get an entity by ID.

        Args:
            entity_id: The entity ID

        Returns:
            The entity or None if not found
        """
        return self.session.get(Entity, entity_id)

    def list(
        self,
        entity_type: str | None = None,
        authority_id: str | None = None,
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Entity]:
        """List entities with optional filtering.

        Args:
            entity_type: Filter by entity type
            authority_id: Filter by authority
            query: Search query (matches name field)
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            List of matching entities
        """
        stmt = select(Entity)

        if entity_type:
            stmt = stmt.where(Entity.type == entity_type)

        if authority_id:
            stmt = stmt.where(Entity.authority_id == authority_id)

        if query:
            # Search in the name field of the JSONB data
            stmt = stmt.where(Entity.data["name"].astext.ilike(f"%{query}%"))

        stmt = stmt.order_by(Entity.created_at.desc()).limit(limit).offset(offset)

        return list(self.session.execute(stmt).scalars().all())

    def count(
        self,
        entity_type: str | None = None,
        authority_id: str | None = None,
    ) -> int:
        """Count entities with optional filtering.

        Args:
            entity_type: Filter by entity type
            authority_id: Filter by authority

        Returns:
            Count of matching entities
        """
        stmt = select(func.count()).select_from(Entity)

        if entity_type:
            stmt = stmt.where(Entity.type == entity_type)

        if authority_id:
            stmt = stmt.where(Entity.authority_id == authority_id)

        return self.session.execute(stmt).scalar() or 0

    def upsert(
        self,
        data: dict[str, Any],
        entity_type: str | None = None,
        authority_id: str | None = None,
        schema_version: str = "v0.1",
        validate: bool = True,
        log_event: bool = True,
    ) -> Entity:
        """Insert or update an entity.

        Args:
            data: Entity data
            entity_type: Entity type (uses data['type'] if not provided)
            authority_id: Authority ID (uses settings if not provided)
            schema_version: Schema version
            validate: Whether to validate against schema
            log_event: Whether to log a changelog event

        Returns:
            The created/updated entity
        """
        # Determine entity type
        if entity_type is None:
            entity_type = data.get("type")
            if entity_type is None:
                raise ValueError("Entity type must be specified")

        # Determine authority
        if authority_id is None:
            settings = get_settings()
            authority_id = settings.instance.id

        # Validate if requested
        if validate:
            validate_entity(data, entity_type, schema_version)

        # Generate ID if not provided
        entity_id = data.get("id")
        if entity_id is None:
            entity_id = make_id(authority_id, entity_type, data)

        # Check for existing entity
        existing = self.get(entity_id)

        # Prepare entity data (separate metadata from payload)
        entity_data = {k: v for k, v in data.items() if k not in ("id", "type", "schema_version", "authority_id")}

        if existing:
            # Update existing entity
            existing.data = entity_data
            existing.schema_version = schema_version
            entity = existing
            event_type = "update_entity"
        else:
            # Create new entity
            entity = Entity(
                id=entity_id,
                type=entity_type,
                schema_version=schema_version,
                authority_id=authority_id,
                data=entity_data,
            )
            self.session.add(entity)
            event_type = "create_entity"

        # Log event
        if log_event:
            append_event(
                self.session,
                event_type=event_type,
                authority_id=authority_id,
                payload={"entity_id": entity_id, "type": entity_type},
            )

        self.session.flush()
        return entity

    def delete(self, entity_id: str, log_event: bool = True) -> bool:
        """Delete an entity.

        Args:
            entity_id: The entity ID to delete
            log_event: Whether to log a changelog event

        Returns:
            True if entity was deleted, False if not found
        """
        entity = self.get(entity_id)
        if entity is None:
            return False

        authority_id = entity.authority_id
        entity_type = entity.type

        self.session.delete(entity)

        if log_event:
            append_event(
                self.session,
                event_type="delete_entity",
                authority_id=authority_id,
                payload={"entity_id": entity_id, "type": entity_type},
            )

        self.session.flush()
        return True

    def get_neighbors(
        self,
        entity_id: str,
        edge_type: str | None = None,
        direction: str = "out",
        limit: int = 100,
    ) -> list[Entity]:
        """Get neighboring entities connected by edges.

        Args:
            entity_id: The source entity ID
            edge_type: Filter by edge type
            direction: 'out' for outgoing edges, 'in' for incoming

        Returns:
            List of connected entities
        """
        from fkg.models.edge import Edge

        if direction == "out":
            # Get entities at the destination of edges from this entity
            edge_stmt = select(Edge.dst_id).where(Edge.src_id == entity_id)
            if edge_type:
                edge_stmt = edge_stmt.where(Edge.type == edge_type)
            edge_stmt = edge_stmt.limit(limit)

            neighbor_ids = [row[0] for row in self.session.execute(edge_stmt).all()]

        else:  # direction == "in"
            # Get entities at the source of edges to this entity
            edge_stmt = select(Edge.src_id).where(Edge.dst_id == entity_id)
            if edge_type:
                edge_stmt = edge_stmt.where(Edge.type == edge_type)
            edge_stmt = edge_stmt.limit(limit)

            neighbor_ids = [row[0] for row in self.session.execute(edge_stmt).all()]

        if not neighbor_ids:
            return []

        # Fetch the entities
        stmt = select(Entity).where(Entity.id.in_(neighbor_ids))
        return list(self.session.execute(stmt).scalars().all())
