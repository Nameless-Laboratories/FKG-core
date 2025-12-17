"""Validation functions for entities and edges."""

from typing import Any

import jsonschema
from jsonschema import Draft7Validator

from fkg.validate.registry import get_registry


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


def validate_entity(
    data: dict[str, Any],
    entity_type: str | None = None,
    version: str = "v0.1",
) -> None:
    """Validate an entity against its schema.

    Args:
        data: The entity data to validate
        entity_type: Entity type. If not provided, uses data['type']
        version: Schema version to validate against

    Raises:
        ValidationError: If validation fails
    """
    # Get entity type from data if not provided
    if entity_type is None:
        entity_type = data.get("type")
        if entity_type is None:
            raise ValidationError("Entity type not specified and not found in data")

    # Get schema
    registry = get_registry()
    try:
        schema = registry.get_entity_schema(entity_type, version)
    except FileNotFoundError:
        raise ValidationError(f"Unknown entity type: {entity_type}")

    # Validate
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "(root)"
            error_messages.append(f"{path}: {error.message}")

        raise ValidationError(
            f"Entity validation failed with {len(errors)} error(s)",
            errors=error_messages,
        )


def validate_edge(data: dict[str, Any], version: str = "v0.1") -> None:
    """Validate an edge against its schema.

    Args:
        data: The edge data to validate
        version: Schema version to validate against

    Raises:
        ValidationError: If validation fails
    """
    registry = get_registry()
    schema = registry.get_edge_schema(version)

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "(root)"
            error_messages.append(f"{path}: {error.message}")

        raise ValidationError(
            f"Edge validation failed with {len(errors)} error(s)",
            errors=error_messages,
        )


def validate_source(data: dict[str, Any], version: str = "v0.1") -> None:
    """Validate a source against its schema.

    Args:
        data: The source data to validate
        version: Schema version to validate against

    Raises:
        ValidationError: If validation fails
    """
    registry = get_registry()
    schema = registry.get_source_schema(version)

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "(root)"
            error_messages.append(f"{path}: {error.message}")

        raise ValidationError(
            f"Source validation failed with {len(errors)} error(s)",
            errors=error_messages,
        )


def validate_manifest(data: dict[str, Any], version: str = "v0.1") -> None:
    """Validate a PKG manifest against its schema.

    Args:
        data: The manifest data to validate
        version: Schema version to validate against

    Raises:
        ValidationError: If validation fails
    """
    registry = get_registry()
    schema = registry.get_manifest_schema(version)

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "(root)"
            error_messages.append(f"{path}: {error.message}")

        raise ValidationError(
            f"Manifest validation failed with {len(errors)} error(s)",
            errors=error_messages,
        )
