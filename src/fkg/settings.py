"""Configuration settings for FKG-Core."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InstanceSettings(BaseModel):
    """Instance identity settings."""

    id: str = "local.dev"
    authority_name: str = "Local Development"
    jurisdiction: str = "Development"
    public_key: str | None = None
    schema_version: str = "v0.1"


class DatabaseSettings(BaseModel):
    """Database connection settings."""

    url: str = "postgresql+psycopg://fkg:fkg@localhost:5432/fkg"


class APISettings(BaseModel):
    """API server settings."""

    host: str = "127.0.0.1"
    port: int = 8000
    cors_enabled: bool = False
    cors_origins: list[str] = Field(default_factory=list)


class RemoteTrust(BaseModel):
    """Trust settings for a remote."""

    verify_signatures: bool = False
    allow_entity_types: list[str] = Field(
        default_factory=lambda: ["organization", "service", "location"]
    )


class RemoteConfig(BaseModel):
    """Configuration for a federated remote."""

    id: str
    endpoint: str
    public_key: str | None = None
    trust: RemoteTrust = Field(default_factory=RemoteTrust)


class FederationSettings(BaseModel):
    """Federation settings."""

    remotes: list[RemoteConfig] = Field(default_factory=list)


class LoggingSettings(BaseModel):
    """Logging settings."""

    level: str = "INFO"
    format: str = "text"


class Settings(BaseSettings):
    """Main settings for FKG-Core."""

    model_config = SettingsConfigDict(
        env_prefix="FKG_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    instance: InstanceSettings = Field(default_factory=InstanceSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    federation: FederationSettings = Field(default_factory=FederationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from a YAML file."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)


def get_schemas_dir() -> Path:
    """Get the path to the schemas directory."""
    # Check relative to package
    pkg_dir = Path(__file__).parent.parent.parent.parent
    schemas_dir = pkg_dir / "schemas"
    if schemas_dir.exists():
        return schemas_dir
    # Check in current working directory
    cwd_schemas = Path.cwd() / "schemas"
    if cwd_schemas.exists():
        return cwd_schemas
    # Fallback
    return schemas_dir


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        # Try to load from config file
        config_paths = [
            Path.cwd() / "fkg.yaml",
            Path.cwd() / "config" / "fkg.yaml",
            Path("/etc/fkg/fkg.yaml"),
        ]
        for path in config_paths:
            if path.exists():
                _settings = Settings.from_yaml(path)
                break
        else:
            _settings = Settings()
    return _settings


def set_settings(settings: Settings) -> None:
    """Set the global settings instance."""
    global _settings
    _settings = settings


def load_settings_from_yaml(path: Path) -> Settings:
    """Load and set settings from a YAML file."""
    settings = Settings.from_yaml(path)
    set_settings(settings)
    return settings
