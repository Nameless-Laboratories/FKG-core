"""Source model for provenance tracking."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fkg.models.base import Base


class Source(Base):
    """A data source for provenance tracking.

    Sources track where entity data originated from.
    """

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        """Convert source to dictionary for API responses."""
        return {
            "id": self.id,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_export_dict(self) -> dict:
        """Convert source to dictionary for PKG export."""
        return {
            "id": self.id,
            **self.data,
        }
