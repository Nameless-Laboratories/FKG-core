"""Edge model for the knowledge graph."""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fkg.models.base import Base


class Edge(Base):
    """An edge (relationship) in the knowledge graph.

    Edges connect two entities with a typed relationship.
    """

    __tablename__ = "edges"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    src_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    dst_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String, nullable=False, default="v0.1")
    authority_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_edges_src_type", "src_id", "type"),
        Index("ix_edges_dst_type", "dst_id", "type"),
        Index("ix_edges_authority_type", "authority_id", "type"),
    )

    def to_dict(self) -> dict:
        """Convert edge to dictionary for API responses."""
        return {
            "id": self.id,
            "type": self.type,
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "schema_version": self.schema_version,
            "authority_id": self.authority_id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_export_dict(self) -> dict:
        """Convert edge to dictionary for PKG export."""
        return {
            "id": self.id,
            "type": self.type,
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "schema_version": self.schema_version,
            "authority_id": self.authority_id,
            "properties": self.data.get("properties", {}),
        }
