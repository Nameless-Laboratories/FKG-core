"""Event model for append-only changelog."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fkg.models.base import Base


class Event(Base):
    """An event in the append-only changelog.

    Events track all changes to the knowledge graph for auditing and sync.
    """

    __tablename__ = "events"

    seq: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    authority_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        """Convert event to dictionary for API responses."""
        return {
            "seq": self.seq,
            "event_type": self.event_type,
            "authority_id": self.authority_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_export_dict(self) -> dict:
        """Convert event to dictionary for PKG export."""
        return {
            "seq": self.seq,
            "event_type": self.event_type,
            "authority_id": self.authority_id,
            "payload": self.payload,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
