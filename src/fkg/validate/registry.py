"""JSON Schema registry for entity and edge validation."""

import json
from pathlib import Path
from typing import Any

from fkg.settings import get_schemas_dir


class SchemaRegistry:
    """Registry for JSON schemas.

    Loads and caches schemas from the schemas directory.
    """

    def __init__(self, schemas_dir: Path | None = None):
        """Initialize the registry.

        Args:
            schemas_dir: Path to schemas directory. Defaults to auto-detection.
        """
        self._schemas_dir = schemas_dir or get_schemas_dir()
        self._cache: dict[str, dict[str, Any]] = {}

    def _load_schema(self, version: str, name: str) -> dict[str, Any]:
        """Load a schema file.

        Args:
            version: Schema version (e.g., 'v0.1')
            name: Schema name (e.g., 'entity.organization')

        Returns:
            The loaded JSON schema

        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        cache_key = f"{version}/{name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        schema_path = self._schemas_dir / version / f"{name}.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path) as f:
            schema = json.load(f)

        self._cache[cache_key] = schema
        return schema

    def get_entity_schema(self, entity_type: str, version: str = "v0.1") -> dict[str, Any]:
        """Get the schema for an entity type.

        Args:
            entity_type: Entity type (e.g., 'organization', 'service')
            version: Schema version

        Returns:
            The JSON schema for the entity type
        """
        return self._load_schema(version, f"entity.{entity_type}")

    def get_edge_schema(self, version: str = "v0.1") -> dict[str, Any]:
        """Get the edge schema.

        Args:
            version: Schema version

        Returns:
            The JSON schema for edges
        """
        return self._load_schema(version, "edge.schema")

    def get_source_schema(self, version: str = "v0.1") -> dict[str, Any]:
        """Get the source schema.

        Args:
            version: Schema version

        Returns:
            The JSON schema for sources
        """
        return self._load_schema(version, "source.schema")

    def get_manifest_schema(self, version: str = "v0.1") -> dict[str, Any]:
        """Get the PKG manifest schema.

        Args:
            version: Schema version

        Returns:
            The JSON schema for PKG manifests
        """
        return self._load_schema(version, "pkg.manifest")

    def list_entity_types(self, version: str = "v0.1") -> list[str]:
        """List available entity types for a schema version.

        Args:
            version: Schema version

        Returns:
            List of entity type names
        """
        version_dir = self._schemas_dir / version
        if not version_dir.exists():
            return []

        types = []
        for schema_file in version_dir.glob("entity.*.json"):
            # Extract type from filename (e.g., entity.organization.json -> organization)
            parts = schema_file.stem.split(".")
            if len(parts) >= 2:
                types.append(parts[1])

        return sorted(types)

    def list_versions(self) -> list[str]:
        """List available schema versions.

        Returns:
            List of version strings
        """
        if not self._schemas_dir.exists():
            return []

        versions = []
        for version_dir in self._schemas_dir.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("v"):
                versions.append(version_dir.name)

        return sorted(versions)


# Global registry instance
_registry: SchemaRegistry | None = None


def get_registry() -> SchemaRegistry:
    """Get the global schema registry instance."""
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
    return _registry


def set_registry(registry: SchemaRegistry) -> None:
    """Set the global schema registry instance."""
    global _registry
    _registry = registry
