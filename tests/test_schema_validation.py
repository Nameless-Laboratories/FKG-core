"""Tests for schema validation."""

import pytest

from fkg.validate.registry import SchemaRegistry
from fkg.validate.validate import ValidationError, validate_entity, validate_edge


class TestSchemaRegistry:
    """Tests for schema registry."""

    def test_list_entity_types(self, schemas_dir):
        registry = SchemaRegistry(schemas_dir)
        types = registry.list_entity_types("v0.1")
        assert "organization" in types
        assert "service" in types
        assert "location" in types
        assert "person" in types

    def test_list_versions(self, schemas_dir):
        registry = SchemaRegistry(schemas_dir)
        versions = registry.list_versions()
        assert "v0.1" in versions

    def test_get_entity_schema(self, schemas_dir):
        registry = SchemaRegistry(schemas_dir)
        schema = registry.get_entity_schema("organization", "v0.1")
        assert schema["title"] == "Organization Entity"
        assert "properties" in schema

    def test_get_edge_schema(self, schemas_dir):
        registry = SchemaRegistry(schemas_dir)
        schema = registry.get_edge_schema("v0.1")
        assert "properties" in schema
        assert "src_id" in schema["properties"]
        assert "dst_id" in schema["properties"]

    def test_unknown_type_raises(self, schemas_dir):
        registry = SchemaRegistry(schemas_dir)
        with pytest.raises(FileNotFoundError):
            registry.get_entity_schema("nonexistent", "v0.1")


class TestValidateEntity:
    """Tests for entity validation."""

    def test_valid_organization(self, schemas_dir, sample_organization):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        # Should not raise
        validate_entity(sample_organization, "organization", "v0.1")

    def test_valid_service(self, schemas_dir, sample_service):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        validate_entity(sample_service, "service", "v0.1")

    def test_missing_required_field(self, schemas_dir):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        # Missing 'name' which is required
        invalid_org = {
            "type": "organization",
            "description": "No name",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_entity(invalid_org, "organization", "v0.1")

        assert "name" in str(exc_info.value.errors)

    def test_wrong_type_const(self, schemas_dir):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        # type must be "organization" for organization schema
        invalid_org = {
            "type": "service",  # Wrong type
            "name": "Test",
        }

        with pytest.raises(ValidationError):
            validate_entity(invalid_org, "organization", "v0.1")

    def test_type_inferred_from_data(self, schemas_dir, sample_organization):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        # Don't pass entity_type, let it be inferred
        validate_entity(sample_organization)

    def test_unknown_type_raises(self, schemas_dir):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        with pytest.raises(ValidationError):
            validate_entity({"type": "unknown", "name": "test"})


class TestValidateEdge:
    """Tests for edge validation."""

    def test_valid_edge(self, schemas_dir, sample_edge):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        # Add required id field
        edge = {**sample_edge, "id": "test:edge:123"}
        validate_edge(edge, "v0.1")

    def test_missing_src_id(self, schemas_dir):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        invalid_edge = {
            "id": "test:edge:123",
            "type": "ORG_OFFERS_SERVICE",
            "dst_id": "test:service:456",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_edge(invalid_edge, "v0.1")

        assert "src_id" in str(exc_info.value.errors)

    def test_invalid_edge_type(self, schemas_dir):
        from fkg.validate.registry import set_registry, SchemaRegistry
        set_registry(SchemaRegistry(schemas_dir))

        invalid_edge = {
            "id": "test:edge:123",
            "type": "INVALID_TYPE",  # Not in enum
            "src_id": "test:org:123",
            "dst_id": "test:service:456",
        }

        with pytest.raises(ValidationError):
            validate_edge(invalid_edge, "v0.1")
