"""Storage operations for sources and evidence."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from fkg.ids.make_id import make_id
from fkg.models.evidence import Evidence
from fkg.models.source import Source


class SourceStorage:
    """Storage operations for sources and evidence."""

    def __init__(self, session: Session):
        """Initialize with a database session."""
        self.session = session

    def get_source(self, source_id: str) -> Source | None:
        """Get a source by ID.

        Args:
            source_id: The source ID

        Returns:
            The source or None if not found
        """
        return self.session.get(Source, source_id)

    def list_sources(self, limit: int = 100, offset: int = 0) -> list[Source]:
        """List all sources.

        Args:
            limit: Maximum results to return
            offset: Offset for pagination

        Returns:
            List of sources
        """
        stmt = select(Source).order_by(Source.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def count_sources(self) -> int:
        """Count all sources.

        Returns:
            Count of sources
        """
        stmt = select(func.count()).select_from(Source)
        return self.session.execute(stmt).scalar() or 0

    def upsert_source(self, data: dict[str, Any], source_id: str | None = None) -> Source:
        """Insert or update a source.

        Args:
            data: Source data
            source_id: Optional source ID (generated if not provided)

        Returns:
            The created/updated source
        """
        # Generate ID if not provided
        if source_id is None:
            source_id = data.get("id")
        if source_id is None:
            # Generate from source data
            source_id = make_id("source", data.get("type", "unknown"), data)

        # Check for existing source
        existing = self.get_source(source_id)

        # Prepare source data
        source_data = {k: v for k, v in data.items() if k != "id"}

        if existing:
            existing.data = source_data
            source = existing
        else:
            source = Source(id=source_id, data=source_data)
            self.session.add(source)

        self.session.flush()
        return source

    def get_evidence(self, evidence_id: str) -> Evidence | None:
        """Get evidence by ID.

        Args:
            evidence_id: The evidence ID

        Returns:
            The evidence or None if not found
        """
        return self.session.get(Evidence, evidence_id)

    def list_evidence_for_entity(self, entity_id: str) -> list[Evidence]:
        """List all evidence for an entity.

        Args:
            entity_id: The entity ID

        Returns:
            List of evidence records
        """
        stmt = select(Evidence).where(Evidence.entity_id == entity_id)
        return list(self.session.execute(stmt).scalars().all())

    def list_evidence_for_source(self, source_id: str) -> list[Evidence]:
        """List all evidence from a source.

        Args:
            source_id: The source ID

        Returns:
            List of evidence records
        """
        stmt = select(Evidence).where(Evidence.source_id == source_id)
        return list(self.session.execute(stmt).scalars().all())

    def add_evidence(
        self,
        entity_id: str,
        source_id: str,
        confidence: float = 1.0,
        notes: str | None = None,
    ) -> Evidence:
        """Add an evidence record linking an entity to a source.

        Args:
            entity_id: The entity ID
            source_id: The source ID
            confidence: Confidence score (0-1)
            notes: Optional notes

        Returns:
            The created evidence record
        """
        evidence = Evidence(
            id=str(uuid4()),
            entity_id=entity_id,
            source_id=source_id,
            confidence=confidence,
            notes=notes,
        )
        self.session.add(evidence)
        self.session.flush()
        return evidence

    def get_entity_provenance(self, entity_id: str) -> dict[str, Any]:
        """Get full provenance information for an entity.

        Args:
            entity_id: The entity ID

        Returns:
            Dictionary with sources and evidence
        """
        evidence_list = self.list_evidence_for_entity(entity_id)

        sources = []
        for ev in evidence_list:
            source = self.get_source(ev.source_id)
            sources.append({
                "evidence_id": str(ev.id),
                "source_id": ev.source_id,
                "source": source.to_dict() if source else None,
                "confidence": ev.confidence,
                "extracted_at": ev.extracted_at.isoformat() if ev.extracted_at else None,
                "notes": ev.notes,
            })

        # Calculate aggregate confidence
        if sources:
            avg_confidence = sum(s["confidence"] for s in sources) / len(sources)
        else:
            avg_confidence = None

        return {
            "entity_id": entity_id,
            "source_count": len(sources),
            "average_confidence": avg_confidence,
            "sources": sources,
        }
