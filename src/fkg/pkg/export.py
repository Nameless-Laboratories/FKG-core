"""PKG export functionality."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from fkg.changelog.append import get_events_for_export
from fkg.models.edge import Edge
from fkg.models.entity import Entity
from fkg.models.source import Source
from fkg.pkg.manifest import create_manifest, save_manifest
from fkg.settings import get_settings


def export_entities(session: Session, output_path: Path, authority_id: str | None = None) -> int:
    """Export entities to JSONL file.

    Args:
        session: Database session
        output_path: Path to output file
        authority_id: Optional authority filter

    Returns:
        Number of entities exported
    """
    stmt = select(Entity)
    if authority_id:
        stmt = stmt.where(Entity.authority_id == authority_id)
    stmt = stmt.order_by(Entity.id)

    count = 0
    with open(output_path, "w") as f:
        for entity in session.execute(stmt).scalars():
            f.write(json.dumps(entity.to_export_dict()) + "\n")
            count += 1

    return count


def export_edges(session: Session, output_path: Path, authority_id: str | None = None) -> int:
    """Export edges to JSONL file.

    Args:
        session: Database session
        output_path: Path to output file
        authority_id: Optional authority filter

    Returns:
        Number of edges exported
    """
    stmt = select(Edge)
    if authority_id:
        stmt = stmt.where(Edge.authority_id == authority_id)
    stmt = stmt.order_by(Edge.id)

    count = 0
    with open(output_path, "w") as f:
        for edge in session.execute(stmt).scalars():
            f.write(json.dumps(edge.to_export_dict()) + "\n")
            count += 1

    return count


def export_sources(session: Session, output_path: Path) -> int:
    """Export sources to JSONL file.

    Args:
        session: Database session
        output_path: Path to output file

    Returns:
        Number of sources exported
    """
    stmt = select(Source).order_by(Source.id)

    count = 0
    with open(output_path, "w") as f:
        for source in session.execute(stmt).scalars():
            f.write(json.dumps(source.to_export_dict()) + "\n")
            count += 1

    return count


def export_changelog(session: Session, output_path: Path, authority_id: str | None = None) -> int:
    """Export changelog to JSONL file.

    Args:
        session: Database session
        output_path: Path to output file
        authority_id: Optional authority filter

    Returns:
        Number of events exported
    """
    events = get_events_for_export(session, authority_id)

    with open(output_path, "w") as f:
        for event in events:
            f.write(json.dumps(event.to_export_dict()) + "\n")

    return len(events)


def export_pkg(
    session: Session,
    output_dir: Path,
    authority_id: str | None = None,
    include_changelog: bool = True,
) -> dict:
    """Export a complete PKG to a directory.

    Args:
        session: Database session
        output_dir: Directory to export to
        authority_id: Optional authority filter (defaults to local instance)
        include_changelog: Whether to include the changelog

    Returns:
        Export statistics
    """
    # Use local authority if not specified
    if authority_id is None:
        settings = get_settings()
        authority_id = settings.instance.id

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export data files
    entity_count = export_entities(session, output_dir / "entities.jsonl", authority_id)
    edge_count = export_edges(session, output_dir / "edges.jsonl", authority_id)
    source_count = export_sources(session, output_dir / "sources.jsonl")

    changelog_count = 0
    if include_changelog:
        changelog_count = export_changelog(session, output_dir / "changelog.jsonl", authority_id)

    # Create and save manifest
    manifest = create_manifest(
        output_dir,
        entity_count=entity_count,
        edge_count=edge_count,
        source_count=source_count,
        include_changelog=include_changelog,
    )
    save_manifest(manifest, output_dir)

    # Create signatures directory (stub for v0.1)
    signatures_dir = output_dir / "signatures"
    signatures_dir.mkdir(exist_ok=True)

    return {
        "entities": entity_count,
        "edges": edge_count,
        "sources": source_count,
        "changelog": changelog_count,
        "manifest": str(output_dir / "manifest.json"),
    }
