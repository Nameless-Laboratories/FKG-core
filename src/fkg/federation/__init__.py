"""Federation functionality for remote PKG sync."""

from fkg.federation.pull import pull_remote
from fkg.federation.remotes import RemoteRegistry

__all__ = ["pull_remote", "RemoteRegistry"]
