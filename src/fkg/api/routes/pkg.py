"""PKG API endpoints."""

import io
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from fkg.db import get_sync_session
from fkg.pkg.export import export_pkg
from fkg.settings import get_settings

router = APIRouter()


@router.get("/latest")
async def get_latest_pkg():
    """Download the latest PKG as a zip file."""
    settings = get_settings()

    # Create a temporary directory for export
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_dir = Path(tmpdir) / "pkg"

        session = get_sync_session()
        try:
            # Export PKG
            export_pkg(session, pkg_dir, include_changelog=True)
            session.commit()
        finally:
            session.close()

        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in pkg_dir.rglob("*"):
                if file_path.is_file():
                    arc_name = file_path.relative_to(pkg_dir)
                    zf.write(file_path, arc_name)

        zip_buffer.seek(0)

        # Return as streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={settings.instance.id}-pkg-latest.zip"
            },
        )


@router.get("/manifest")
async def get_manifest():
    """Get the current PKG manifest (without downloading full PKG)."""
    import tempfile
    from pathlib import Path

    from fkg.pkg.manifest import create_manifest
    from fkg.storage.edges import EdgeStorage
    from fkg.storage.entities import EntityStorage
    from fkg.storage.sources import SourceStorage

    session = get_sync_session()
    try:
        entity_count = EntityStorage(session).count()
        edge_count = EdgeStorage(session).count()
        source_count = SourceStorage(session).count_sources()

        # Create manifest info without file checksums
        settings = get_settings()
        from datetime import datetime, timezone

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
        }

        return manifest
    finally:
        session.close()
