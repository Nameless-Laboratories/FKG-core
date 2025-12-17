"""Pull PKG from remote federation nodes."""

import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from fkg.pkg.import_ import import_pkg
from fkg.pkg.sign import verify_pkg
from fkg.settings import RemoteConfig


class PullError(Exception):
    """Raised when pull operation fails."""
    pass


def fetch_remote_pkg(remote: RemoteConfig, output_dir: Path) -> Path:
    """Fetch PKG from a remote endpoint.

    Args:
        remote: Remote configuration
        output_dir: Directory to extract PKG to

    Returns:
        Path to the extracted PKG directory

    Raises:
        PullError: If fetch fails
    """
    pkg_url = f"{remote.endpoint.rstrip('/')}/pkg/latest"

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(pkg_url)
            response.raise_for_status()

            # Save zip file
            zip_path = output_dir / "pkg.zip"
            zip_path.write_bytes(response.content)

            # Extract zip
            pkg_dir = output_dir / "pkg"
            pkg_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(pkg_dir)

            return pkg_dir

    except httpx.HTTPError as e:
        raise PullError(f"Failed to fetch PKG from {pkg_url}: {e}")


def pull_remote(
    session: Session,
    remote: RemoteConfig,
    verify_signatures: bool | None = None,
) -> dict[str, Any]:
    """Pull and import PKG from a remote.

    Args:
        session: Database session
        remote: Remote configuration
        verify_signatures: Override signature verification setting

    Returns:
        Import statistics

    Raises:
        PullError: If pull fails
    """
    # Determine signature verification
    if verify_signatures is None:
        verify_signatures = remote.trust.verify_signatures

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Fetch PKG from remote
        pkg_dir = fetch_remote_pkg(remote, tmpdir_path)

        # Verify signature if required
        if verify_signatures:
            verify_result = verify_pkg(pkg_dir, remote.public_key)
            if not verify_result.get("valid"):
                raise PullError(f"Signature verification failed: {verify_result.get('error')}")

        # Import with remote's authority ID
        # This ensures remote entities are namespaced to the remote
        stats = import_pkg(
            session,
            pkg_dir,
            authority=remote.id,
            verify_checksums_flag=True,
            validate=True,
        )

        return stats


def pull_all_remotes(session: Session) -> dict[str, dict[str, Any]]:
    """Pull from all configured remotes.

    Args:
        session: Database session

    Returns:
        Dictionary mapping remote IDs to their import stats
    """
    from fkg.federation.remotes import get_remote_registry

    registry = get_remote_registry()
    results = {}

    for remote in registry.list():
        try:
            stats = pull_remote(session, remote)
            results[remote.id] = {
                "success": True,
                "stats": stats,
            }
        except Exception as e:
            results[remote.id] = {
                "success": False,
                "error": str(e),
            }

    return results
