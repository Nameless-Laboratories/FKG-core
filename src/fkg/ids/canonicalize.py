"""Canonicalization utilities for deterministic ID generation."""

import json
import re
import unicodedata
from typing import Any


def normalize_string(s: str) -> str:
    """Normalize a string for comparison.

    - Unicode normalize (NFKC)
    - Lowercase
    - Strip leading/trailing whitespace
    - Collapse internal whitespace
    - Remove punctuation that commonly varies
    """
    if not isinstance(s, str):
        return s

    # Unicode normalization
    s = unicodedata.normalize("NFKC", s)

    # Lowercase
    s = s.lower()

    # Strip and collapse whitespace
    s = " ".join(s.split())

    return s


def normalize_name(name: str) -> str:
    """Normalize an organization/person/service name.

    More aggressive normalization for names:
    - All normalize_string operations
    - Remove common suffixes (Inc, LLC, etc.)
    - Remove punctuation
    """
    if not isinstance(name, str):
        return name

    s = normalize_string(name)

    # Remove common business suffixes
    suffixes = [
        r"\s+inc\.?$",
        r"\s+llc\.?$",
        r"\s+corp\.?$",
        r"\s+corporation$",
        r"\s+incorporated$",
        r"\s+ltd\.?$",
        r"\s+limited$",
        r"\s+co\.?$",
        r"\s+company$",
    ]
    for suffix in suffixes:
        s = re.sub(suffix, "", s, flags=re.IGNORECASE)

    # Remove punctuation (keep alphanumeric and spaces)
    s = re.sub(r"[^\w\s]", "", s)

    # Final whitespace cleanup
    s = " ".join(s.split())

    return s


def sort_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively sort dictionary keys."""
    result = {}
    for key in sorted(d.keys()):
        value = d[key]
        if isinstance(value, dict):
            result[key] = sort_dict(value)
        elif isinstance(value, list):
            result[key] = [sort_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result


def canonicalize(payload: dict[str, Any], normalize_names: bool = True) -> dict[str, Any]:
    """Canonicalize a payload for deterministic hashing.

    Operations:
    - Sort keys recursively
    - Normalize string values (lowercase, collapse whitespace)
    - Special handling for 'name' field if normalize_names=True
    - Remove null values
    - Remove empty strings and empty collections

    Args:
        payload: The dictionary to canonicalize
        normalize_names: Whether to apply aggressive name normalization

    Returns:
        Canonicalized dictionary
    """
    if not isinstance(payload, dict):
        return payload

    result = {}

    for key in sorted(payload.keys()):
        value = payload[key]

        # Skip null/None values
        if value is None:
            continue

        # Handle nested structures
        if isinstance(value, dict):
            canonical_value = canonicalize(value, normalize_names)
            if canonical_value:  # Skip empty dicts
                result[key] = canonical_value

        elif isinstance(value, list):
            # Process list items
            canonical_list = []
            for item in value:
                if isinstance(item, dict):
                    canonical_item = canonicalize(item, normalize_names)
                    if canonical_item:
                        canonical_list.append(canonical_item)
                elif isinstance(item, str):
                    normalized = normalize_string(item)
                    if normalized:
                        canonical_list.append(normalized)
                elif item is not None:
                    canonical_list.append(item)

            if canonical_list:  # Skip empty lists
                result[key] = canonical_list

        elif isinstance(value, str):
            # Apply name normalization for specific fields
            if normalize_names and key in ("name", "organization_name", "service_name"):
                normalized = normalize_name(value)
            else:
                normalized = normalize_string(value)

            if normalized:  # Skip empty strings
                result[key] = normalized

        else:
            # Numbers, booleans, etc.
            result[key] = value

    return result


def canonical_json(payload: dict[str, Any]) -> str:
    """Convert payload to canonical JSON string.

    Returns a deterministic JSON representation suitable for hashing.
    """
    canonical = canonicalize(payload)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
