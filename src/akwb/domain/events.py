"""Domain events used to decouple engines and services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from akwb.types import make_id, utc_now


@dataclass(kw_only=True, frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=make_id)
    timestamp: str = field(default_factory=utc_now)
    version: int = 1


@dataclass(kw_only=True, frozen=True)
class WorkspaceInitialized(DomainEvent):
    """Emitted when a workspace is successfully bootstrapped."""

    project_root: str
    workspace_dir: str


@dataclass(kw_only=True, frozen=True)
class ConfigLoaded(DomainEvent):
    """Emitted when the effective configuration is resolved."""

    config_snapshot: dict[str, Any]


@dataclass(kw_only=True, frozen=True)
class PluginLoaded(DomainEvent):
    """Emitted when a plugin is loaded and validated."""

    plugin_name: str
    plugin_version: str
    ports: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass(kw_only=True, frozen=True)
class StorageWritten(DomainEvent):
    """Emitted when the storage backend writes a file."""

    relative_path: str
    mime_type: str


@dataclass(kw_only=True, frozen=True)
class DiagnosticEmitted(DomainEvent):
    """Emitted when a diagnostic is produced."""

    level: str
    code: str
    message: str
    source_ref: str | None = None


@dataclass(kw_only=True, frozen=True)
class ArtifactDiscovered(DomainEvent):
    """Emitted when a project artifact is discovered."""

    artifact_id: str
    relative_path: str
    artifact_type: str
    category: str


@dataclass(kw_only=True, frozen=True)
class DiscoveryCompleted(DomainEvent):
    """Emitted when the discovery engine finishes scanning the project."""

    project_root: str
    artifact_count: int
    registry_path: str
