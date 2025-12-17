"""Remote registry for federation."""

from fkg.settings import RemoteConfig, get_settings


class RemoteRegistry:
    """Registry for federation remotes."""

    def __init__(self):
        """Initialize the registry from settings."""
        self._remotes: dict[str, RemoteConfig] = {}
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        """Load remotes from settings."""
        settings = get_settings()
        for remote in settings.federation.remotes:
            self._remotes[remote.id] = remote

    def get(self, remote_id: str) -> RemoteConfig | None:
        """Get a remote configuration by ID."""
        return self._remotes.get(remote_id)

    def list(self) -> list[RemoteConfig]:
        """List all configured remotes."""
        return list(self._remotes.values())

    def add(self, config: RemoteConfig) -> None:
        """Add a remote configuration.

        Note: This only adds to the in-memory registry.
        Persistence would require modifying the config file.
        """
        self._remotes[config.id] = config

    def remove(self, remote_id: str) -> bool:
        """Remove a remote configuration.

        Returns True if remote was removed, False if not found.
        """
        if remote_id in self._remotes:
            del self._remotes[remote_id]
            return True
        return False

    def is_entity_type_allowed(self, remote_id: str, entity_type: str) -> bool:
        """Check if an entity type is allowed from a remote."""
        remote = self.get(remote_id)
        if remote is None:
            return False
        return entity_type in remote.trust.allow_entity_types


# Global registry instance
_registry: RemoteRegistry | None = None


def get_remote_registry() -> RemoteRegistry:
    """Get the global remote registry instance."""
    global _registry
    if _registry is None:
        _registry = RemoteRegistry()
    return _registry
