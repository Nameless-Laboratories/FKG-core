"""Deterministic ID generation for entities and edges."""

import hashlib
from typing import Any

from fkg.ids.canonicalize import canonical_json, canonicalize


def make_id(namespace: str, entity_type: str, payload: dict[str, Any]) -> str:
    """Generate a deterministic ID for an entity or edge.

    The ID format is: {namespace}:{type}:{hash[:16]}

    The hash is computed from the canonical JSON representation of the payload,
    ensuring that equivalent payloads produce the same ID.

    Args:
        namespace: The authority namespace (e.g., 'mrn.marin.ca.us')
        entity_type: The entity type (e.g., 'organization', 'service')
        payload: The entity payload to hash

    Returns:
        A deterministic ID string
    """
    # Remove id from payload if present (we're generating it)
    payload_for_hash = {k: v for k, v in payload.items() if k not in ("id", "authority_id")}

    # Get canonical JSON
    canonical = canonical_json(payload_for_hash)

    # Compute SHA256 hash
    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # Use first 16 characters of hash
    short_hash = hash_bytes[:16]

    return f"{namespace}:{entity_type}:{short_hash}"


def make_edge_id(
    namespace: str, edge_type: str, src_id: str, dst_id: str, properties: dict[str, Any] | None = None
) -> str:
    """Generate a deterministic ID for an edge.

    Edge IDs are based on the source, destination, type, and properties.

    Args:
        namespace: The authority namespace
        edge_type: The edge type (e.g., 'ORG_OFFERS_SERVICE')
        src_id: Source entity ID
        dst_id: Destination entity ID
        properties: Optional edge properties

    Returns:
        A deterministic edge ID string
    """
    payload = {
        "type": edge_type,
        "src_id": src_id,
        "dst_id": dst_id,
    }
    if properties:
        payload["properties"] = properties

    canonical = canonical_json(payload)
    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    short_hash = hash_bytes[:16]

    return f"{namespace}:edge:{short_hash}"


def compute_content_hash(payload: dict[str, Any]) -> str:
    """Compute a content hash for change detection.

    Returns the full SHA256 hash of the canonical payload.
    """
    canonical = canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
