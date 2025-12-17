"""PKG signing and verification (stub for v0.1)."""

from pathlib import Path
from typing import Any

from fkg.pkg.manifest import load_manifest


class SignatureError(Exception):
    """Raised when signature operations fail."""
    pass


def sign_pkg(pkg_dir: Path, private_key: str | None = None) -> dict[str, Any]:
    """Sign a PKG with the instance's private key.

    NOTE: This is a stub for v0.1. Full signature implementation
    would use Ed25519 or similar.

    Args:
        pkg_dir: Path to PKG directory
        private_key: Private key for signing (optional in v0.1)

    Returns:
        Signature information
    """
    # Load manifest
    manifest = load_manifest(pkg_dir)

    # For v0.1, we just create a placeholder signature file
    signatures_dir = pkg_dir / "signatures"
    signatures_dir.mkdir(exist_ok=True)

    signature_info = {
        "algorithm": "ed25519",
        "signed": False,  # v0.1 stub
        "message": "Signature not implemented in v0.1",
    }

    # Write placeholder signature file
    sig_file = signatures_dir / "manifest.sig"
    sig_file.write_text("SIGNATURE_PLACEHOLDER_V0.1")

    return signature_info


def verify_pkg(pkg_dir: Path, public_key: str | None = None) -> dict[str, Any]:
    """Verify a PKG signature.

    NOTE: This is a stub for v0.1. Always returns success with a warning.

    Args:
        pkg_dir: Path to PKG directory
        public_key: Public key for verification (optional in v0.1)

    Returns:
        Verification result
    """
    # Load manifest
    try:
        manifest = load_manifest(pkg_dir)
    except Exception as e:
        return {
            "valid": False,
            "error": f"Failed to load manifest: {e}",
        }

    # Check if signature file exists
    sig_file = pkg_dir / "signatures" / "manifest.sig"

    result = {
        "valid": True,  # v0.1 stub always passes
        "verified": False,  # But not actually cryptographically verified
        "warning": "Signature verification not implemented in v0.1",
        "signature_file_exists": sig_file.exists(),
    }

    return result


def generate_keypair() -> dict[str, str]:
    """Generate a new Ed25519 keypair.

    NOTE: This is a stub for v0.1.

    Returns:
        Dictionary with public_key and private_key
    """
    # Stub implementation
    return {
        "public_key": "ed25519:STUB_PUBLIC_KEY_V0.1",
        "private_key": "ed25519:STUB_PRIVATE_KEY_V0.1",
        "warning": "Key generation not implemented in v0.1",
    }
