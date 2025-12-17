"""PKG import functionality."""

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from fkg.pkg.manifest import load_manifest, verify_checksums
from fkg.storage.edges import EdgeStorage
from fkg.storage.entities import EntityStorage
from fkg.storage.sources import SourceStorage
from fkg.settings import get_settings


class ImportError(Exception):
    """Raised when PKG import fails."""
    pass


def import_entities(
    session: Session,
    input_path: Path,
    authority_id: str,
    validate: bool = True,
) -> int:
    """Import entities from JSONL file.

    Args:
        session: Database session
        input_path: Path to JSONL file
        authority_id: Authority ID to assign to imported entities
        validate: Whether to validate against schema

    Returns:
        Number of entities imported
    """
    storage = EntityStorage(session)
    count = 0

    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)

            # Use the authority_id from import, not from the data
            storage.upsert(
                data=data,
                entity_type=data.get("type"),
                authority_id=authority_id,
                schema_version=data.get("schema_version", "v0.1"),
                validate=validate,
                log_event=True,
            )
            count += 1

    return count


def import_edges(
    session: Session,
    input_path: Path,
    authority_id: str,
    validate: bool = True,
) -> int:
    """Import edges from JSONL file.

    Args:
        session: Database session
        input_path: Path to JSONL file
        authority_id: Authority ID to assign to imported edges
        validate: Whether to validate against schema

    Returns:
        Number of edges imported
    """
    storage = EdgeStorage(session)
    count = 0

    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)

            storage.upsert(
                data=data,
                authority_id=authority_id,
                schema_version=data.get("schema_version", "v0.1"),
                validate=validate,
                log_event=True,
            )
            count += 1

    return count


def import_sources(session: Session, input_path: Path) -> int:
    """Import sources from JSONL file.

    Args:
        session: Database session
        input_path: Path to JSONL file

    Returns:
        Number of sources imported
    """
    storage = SourceStorage(session)
    count = 0

    with open(input_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)
            storage.upsert_source(data)
            count += 1

    return count


def import_pkg(
    session: Session,
    pkg_dir: Path,
    authority: str = "local",
    verify_checksums_flag: bool = True,
    validate: bool = True,
) -> dict[str, Any]:
    """Import a PKG from a directory.

    Args:
        session: Database session
        pkg_dir: Path to PKG directory
        authority: 'local' to use local instance ID, or a remote authority ID
        verify_checksums_flag: Whether to verify file checksums
        validate: Whether to validate entities/edges against schema

    Returns:
        Import statistics

    Raises:
        ImportError: If import fails
    """
    # Load and validate manifest
    manifest = load_manifest(pkg_dir)

    # Verify checksums if requested
    if verify_checksums_flag:
        mismatches = verify_checksums(pkg_dir, manifest)
        if mismatches:
            raise ImportError(f"Checksum verification failed: {', '.join(mismatches)}")

    # Determine authority ID
    if authority == "local":
        settings = get_settings()
        authority_id = settings.instance.id
    else:
        authority_id = authority

    # Import files
    files = manifest.get("files", {})
    stats = {
        "entities": 0,
        "edges": 0,
        "sources": 0,
        "authority_id": authority_id,
    }

    # Import sources first (they may be referenced by entities)
    if "sources" in files:
        sources_path = pkg_dir / files["sources"]
        if sources_path.exists():
            stats["sources"] = import_sources(session, sources_path)

    # Import entities
    if "entities" in files:
        entities_path = pkg_dir / files["entities"]
        if entities_path.exists():
            stats["entities"] = import_entities(
                session, entities_path, authority_id, validate
            )

    # Import edges
    if "edges" in files:
        edges_path = pkg_dir / files["edges"]
        if edges_path.exists():
            stats["edges"] = import_edges(
                session, edges_path, authority_id, validate
            )

    session.commit()
    return stats


def validate_pkg(pkg_dir: Path) -> dict[str, Any]:
    """Validate a PKG without importing.

    Args:
        pkg_dir: Path to PKG directory

    Returns:
        Validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "manifest": None,
    }

    # Check manifest
    try:
        manifest = load_manifest(pkg_dir)
        results["manifest"] = manifest
    except FileNotFoundError as e:
        results["valid"] = False
        results["errors"].append(str(e))
        return results
    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Invalid manifest: {e}")
        return results

    # Verify checksums
    mismatches = verify_checksums(pkg_dir, manifest)
    if mismatches:
        results["valid"] = False
        results["errors"].extend(mismatches)

    # Check required files exist
    files = manifest.get("files", {})
    for file_key, filename in files.items():
        file_path = pkg_dir / filename
        if not file_path.exists():
            results["warnings"].append(f"Listed file missing: {filename}")

    return results
