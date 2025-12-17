"""Tests for PKG export/import roundtrip."""

import json
import tempfile
from pathlib import Path

import pytest


class TestPkgRoundtrip:
    """Tests for PKG roundtrip operations."""

    def test_manifest_creation(self):
        """Test manifest is created correctly."""
        from fkg.pkg.manifest import create_manifest, save_manifest, load_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create empty files to simulate export
            (output_dir / "entities.jsonl").write_text("")
            (output_dir / "edges.jsonl").write_text("")
            (output_dir / "sources.jsonl").write_text("")

            manifest = create_manifest(
                output_dir,
                entity_count=10,
                edge_count=5,
                source_count=2,
            )

            assert manifest["version"] == "0.1"
            assert manifest["counts"]["entities"] == 10
            assert manifest["counts"]["edges"] == 5
            assert manifest["counts"]["sources"] == 2

            # Save and reload
            save_manifest(manifest, output_dir)
            loaded = load_manifest(output_dir)

            assert loaded["version"] == manifest["version"]
            assert loaded["counts"] == manifest["counts"]

    def test_checksum_verification(self):
        """Test checksum verification."""
        from fkg.pkg.manifest import (
            create_manifest,
            save_manifest,
            verify_checksums,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create files with content
            (output_dir / "entities.jsonl").write_text('{"id": "test"}\n')
            (output_dir / "edges.jsonl").write_text("")
            (output_dir / "sources.jsonl").write_text("")

            manifest = create_manifest(output_dir, 1, 0, 0)
            save_manifest(manifest, output_dir)

            # Verify checksums pass
            mismatches = verify_checksums(output_dir, manifest)
            assert len(mismatches) == 0

            # Modify file
            (output_dir / "entities.jsonl").write_text('{"id": "modified"}\n')

            # Verify checksums fail
            mismatches = verify_checksums(output_dir, manifest)
            assert len(mismatches) == 1
            assert "entities.jsonl" in mismatches[0]

    def test_validate_pkg(self):
        """Test PKG validation."""
        from fkg.pkg.import_ import validate_pkg
        from fkg.pkg.manifest import create_manifest, save_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create a valid PKG structure
            (output_dir / "entities.jsonl").write_text("")
            (output_dir / "edges.jsonl").write_text("")
            (output_dir / "sources.jsonl").write_text("")

            manifest = create_manifest(output_dir, 0, 0, 0)
            save_manifest(manifest, output_dir)

            # Validate
            results = validate_pkg(output_dir)
            assert results["valid"] is True
            assert len(results["errors"]) == 0

    def test_validate_pkg_missing_manifest(self):
        """Test PKG validation fails with missing manifest."""
        from fkg.pkg.import_ import validate_pkg

        with tempfile.TemporaryDirectory() as tmpdir:
            results = validate_pkg(Path(tmpdir))
            assert results["valid"] is False
            assert any("manifest" in e.lower() for e in results["errors"])


class TestJsonlFormat:
    """Tests for JSONL file format."""

    def test_entities_jsonl_format(self, sample_organization):
        """Test entity JSONL format."""
        # Simulate export format
        export_data = {
            "id": "test:organization:abc123",
            "type": "organization",
            "schema_version": "v0.1",
            "authority_id": "test.local",
            **{k: v for k, v in sample_organization.items() if k != "type"},
        }

        jsonl_line = json.dumps(export_data)

        # Should be valid JSON
        parsed = json.loads(jsonl_line)
        assert parsed["id"] == "test:organization:abc123"
        assert parsed["type"] == "organization"
        assert parsed["name"] == sample_organization["name"]

    def test_edges_jsonl_format(self, sample_edge):
        """Test edge JSONL format."""
        export_data = {
            "id": "test:edge:abc123",
            "type": sample_edge["type"],
            "src_id": sample_edge["src_id"],
            "dst_id": sample_edge["dst_id"],
            "schema_version": "v0.1",
            "authority_id": "test.local",
            "properties": sample_edge.get("properties", {}),
        }

        jsonl_line = json.dumps(export_data)
        parsed = json.loads(jsonl_line)

        assert parsed["type"] == "ORG_OFFERS_SERVICE"
        assert parsed["src_id"] == sample_edge["src_id"]
        assert parsed["dst_id"] == sample_edge["dst_id"]
