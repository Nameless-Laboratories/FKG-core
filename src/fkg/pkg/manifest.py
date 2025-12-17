"""PKG manifest handling."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fkg.settings import get_settings
from fkg.validate.validate import validate_manifest


def compute_file_checksum(path: Path) -> str:
    """Compute SHA256 checksum of a file.

    Args:
        path: Path to the file

    Returns:
        Hex-encoded SHA256 checksum
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def create_manifest(
    output_dir: Path,
    entity_count: int,
    edge_count: int,
    source_count: int,
    include_changelog: bool = False,
) -> dict[str, Any]:
    """Create a PKG manifest.

    Args:
        output_dir: Directory containing the PKG files
        entity_count: Number of entities in the PKG
        edge_count: Number of edges in the PKG
        source_count: Number of sources in the PKG
        include_changelog: Whether changelog is included

    Returns:
        The manifest dictionary
    """
    settings = get_settings()

    manifest = {
        "version": "0.1",
        "authority_id": settings.instance.id,
        "authority_name": settings.instance.authority_name,
        "jurisdiction": settings.instance.jurisdiction,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": settings.instance.schema_version,
        "counts": {
            "entities": entity_count,
            "edges": edge_count,
            "sources": source_count,
        },
        "files": {
            "entities": "entities.jsonl",
            "edges": "edges.jsonl",
            "sources": "sources.jsonl",
        },
        "checksums": {},
    }

    if include_changelog:
        manifest["files"]["changelog"] = "changelog.jsonl"

    # Compute checksums for all files
    for file_key, filename in manifest["files"].items():
        file_path = output_dir / filename
        if file_path.exists():
            manifest["checksums"][filename] = compute_file_checksum(file_path)

    return manifest


def save_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
    """Save manifest to file.

    Args:
        manifest: The manifest dictionary
        output_dir: Directory to save to

    Returns:
        Path to the saved manifest file
    """
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


def load_manifest(pkg_dir: Path) -> dict[str, Any]:
    """Load manifest from a PKG directory.

    Args:
        pkg_dir: Path to the PKG directory

    Returns:
        The loaded manifest

    Raises:
        FileNotFoundError: If manifest doesn't exist
        ValidationError: If manifest is invalid
    """
    manifest_path = pkg_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Validate manifest
    validate_manifest(manifest)

    return manifest


def verify_checksums(pkg_dir: Path, manifest: dict[str, Any]) -> list[str]:
    """Verify file checksums against manifest.

    Args:
        pkg_dir: Path to the PKG directory
        manifest: The manifest dictionary

    Returns:
        List of files with checksum mismatches (empty if all match)
    """
    mismatches = []
    checksums = manifest.get("checksums", {})

    for filename, expected_checksum in checksums.items():
        file_path = pkg_dir / filename
        if not file_path.exists():
            mismatches.append(f"{filename}: file missing")
            continue

        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum != expected_checksum:
            mismatches.append(f"{filename}: checksum mismatch")

    return mismatches
