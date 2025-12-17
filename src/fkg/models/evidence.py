"""Evidence model for provenance tracking."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from fkg.models.base import Base


class Evidence(Base):
    """Evidence linking an entity to a source.

    Evidence records track the relationship between entities and their data sources,
    including confidence scores.
    """

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    entity_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        """Convert evidence to dictionary for API responses."""
        return {
            "id": str(self.id),
            "entity_id": self.entity_id,
            "source_id": self.source_id,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "notes": self.notes,
        }
