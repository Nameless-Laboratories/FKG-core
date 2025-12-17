"""Provenance scoring utilities."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ProvenanceScore:
    """Provenance score for an entity."""

    confidence: float
    source_count: int
    source_types: list[str]
    recency_days: float | None


def calculate_confidence(evidence_records: list[dict[str, Any]]) -> ProvenanceScore:
    """Calculate a confidence score from evidence records.

    This is a simple scoring model for v0.1:
    - Base confidence is the average of all evidence confidence scores
    - Bonus for multiple sources (diversity)
    - No penalty for age in v0.1 (could add later)

    Args:
        evidence_records: List of evidence records with 'confidence' and 'source' fields

    Returns:
        ProvenanceScore with calculated values
    """
    if not evidence_records:
        return ProvenanceScore(
            confidence=0.0,
            source_count=0,
            source_types=[],
            recency_days=None,
        )

    # Calculate average confidence
    confidences = [e.get("confidence", 1.0) for e in evidence_records]
    avg_confidence = sum(confidences) / len(confidences)

    # Gather source types
    source_types = set()
    for e in evidence_records:
        source = e.get("source", {})
        if isinstance(source, dict):
            source_type = source.get("data", {}).get("type") or source.get("type")
            if source_type:
                source_types.add(source_type)

    # Diversity bonus: up to 0.1 bonus for having multiple source types
    diversity_bonus = min(0.1, (len(source_types) - 1) * 0.05) if len(source_types) > 1 else 0

    # Final confidence (capped at 1.0)
    final_confidence = min(1.0, avg_confidence + diversity_bonus)

    return ProvenanceScore(
        confidence=round(final_confidence, 3),
        source_count=len(evidence_records),
        source_types=sorted(source_types),
        recency_days=None,  # Not implemented in v0.1
    )


def get_source_weight(source_type: str) -> float:
    """Get the weight for a source type.

    Different source types may have different reliability weights.
    This is a simple implementation for v0.1.

    Args:
        source_type: The source type

    Returns:
        Weight multiplier (0.0 - 1.0)
    """
    weights = {
        "api": 0.9,
        "dataset": 0.9,
        "url": 0.7,
        "file": 0.7,
        "manual": 0.8,
    }
    return weights.get(source_type, 0.5)
