"""Tests for ID generation and canonicalization."""

import pytest

from fkg.ids.canonicalize import canonicalize, canonical_json, normalize_name, normalize_string
from fkg.ids.make_id import make_id, make_edge_id, compute_content_hash


class TestNormalizeString:
    """Tests for string normalization."""

    def test_lowercase(self):
        assert normalize_string("Hello World") == "hello world"

    def test_whitespace_collapse(self):
        assert normalize_string("hello   world") == "hello world"
        assert normalize_string("  hello  world  ") == "hello world"

    def test_unicode_normalize(self):
        # NFKC normalization
        assert normalize_string("café") == "café"

    def test_empty_string(self):
        assert normalize_string("") == ""

    def test_non_string(self):
        assert normalize_string(123) == 123


class TestNormalizeName:
    """Tests for name normalization."""

    def test_remove_inc(self):
        assert normalize_name("Acme Inc.") == "acme"
        assert normalize_name("Acme Inc") == "acme"

    def test_remove_llc(self):
        assert normalize_name("Acme LLC") == "acme"

    def test_remove_corp(self):
        assert normalize_name("Acme Corp.") == "acme"
        assert normalize_name("Acme Corporation") == "acme"

    def test_remove_punctuation(self):
        assert normalize_name("O'Brien & Associates") == "obrien associates"

    def test_preserves_meaningful_content(self):
        assert normalize_name("Marin Food Bank") == "marin food bank"


class TestCanonicalize:
    """Tests for payload canonicalization."""

    def test_sorts_keys(self):
        payload = {"z": 1, "a": 2, "m": 3}
        result = canonicalize(payload, normalize_names=False)
        assert list(result.keys()) == ["a", "m", "z"]

    def test_removes_null_values(self):
        payload = {"name": "test", "description": None}
        result = canonicalize(payload, normalize_names=False)
        assert "description" not in result

    def test_removes_empty_strings(self):
        payload = {"name": "test", "notes": ""}
        result = canonicalize(payload, normalize_names=False)
        assert "notes" not in result

    def test_normalizes_name_field(self):
        payload = {"name": "Test Organization Inc.", "type": "organization"}
        result = canonicalize(payload, normalize_names=True)
        assert result["name"] == "test organization"

    def test_nested_dict(self):
        payload = {"contact": {"z_field": "a", "a_field": "b"}}
        result = canonicalize(payload, normalize_names=False)
        assert list(result["contact"].keys()) == ["a_field", "z_field"]

    def test_list_of_strings(self):
        payload = {"tags": ["  FOOD  ", "Housing", "healthcare"]}
        result = canonicalize(payload, normalize_names=False)
        assert result["tags"] == ["food", "housing", "healthcare"]


class TestCanonicalJson:
    """Tests for canonical JSON generation."""

    def test_deterministic(self):
        payload = {"b": 2, "a": 1, "c": {"y": 1, "x": 2}}
        json1 = canonical_json(payload)
        json2 = canonical_json(payload)
        assert json1 == json2

    def test_no_extra_whitespace(self):
        payload = {"a": 1, "b": 2}
        result = canonical_json(payload)
        assert " " not in result  # No spaces in compact JSON


class TestMakeId:
    """Tests for ID generation."""

    def test_deterministic_id(self):
        """Same payload should produce same ID."""
        payload = {"name": "Test Org", "type": "organization"}
        id1 = make_id("test.local", "organization", payload)
        id2 = make_id("test.local", "organization", payload)
        assert id1 == id2

    def test_format(self):
        """ID should follow namespace:type:hash format."""
        payload = {"name": "Test Org", "type": "organization"}
        entity_id = make_id("test.local", "organization", payload)
        parts = entity_id.split(":")
        assert len(parts) == 3
        assert parts[0] == "test.local"
        assert parts[1] == "organization"
        assert len(parts[2]) == 16  # Short hash

    def test_whitespace_normalization(self):
        """Whitespace differences should not affect ID."""
        payload1 = {"name": "Test Org", "description": "hello world"}
        payload2 = {"name": "  Test Org  ", "description": "hello   world"}
        id1 = make_id("test.local", "organization", payload1)
        id2 = make_id("test.local", "organization", payload2)
        assert id1 == id2

    def test_different_content_different_id(self):
        """Different content should produce different IDs."""
        payload1 = {"name": "Test Org A"}
        payload2 = {"name": "Test Org B"}
        id1 = make_id("test.local", "organization", payload1)
        id2 = make_id("test.local", "organization", payload2)
        assert id1 != id2


class TestMakeEdgeId:
    """Tests for edge ID generation."""

    def test_deterministic(self):
        """Same edge should produce same ID."""
        id1 = make_edge_id("test", "ORG_OFFERS_SERVICE", "src:1", "dst:1")
        id2 = make_edge_id("test", "ORG_OFFERS_SERVICE", "src:1", "dst:1")
        assert id1 == id2

    def test_different_endpoints(self):
        """Different endpoints should produce different IDs."""
        id1 = make_edge_id("test", "ORG_OFFERS_SERVICE", "src:1", "dst:1")
        id2 = make_edge_id("test", "ORG_OFFERS_SERVICE", "src:1", "dst:2")
        assert id1 != id2

    def test_format(self):
        """Edge ID should follow namespace:edge:hash format."""
        edge_id = make_edge_id("test.local", "ORG_OFFERS_SERVICE", "src:1", "dst:1")
        parts = edge_id.split(":")
        assert parts[0] == "test.local"
        assert parts[1] == "edge"


class TestComputeContentHash:
    """Tests for content hash computation."""

    def test_deterministic(self):
        payload = {"name": "Test", "value": 123}
        hash1 = compute_content_hash(payload)
        hash2 = compute_content_hash(payload)
        assert hash1 == hash2

    def test_full_length(self):
        payload = {"name": "Test"}
        content_hash = compute_content_hash(payload)
        assert len(content_hash) == 64  # Full SHA256 hex
