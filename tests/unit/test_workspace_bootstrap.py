"""Tests for workspace bootstrap."""

from pathlib import Path

from akwb.config import Config
from akwb.events import InMemoryEventBus
from akwb.observability import LoggerObservability
from akwb.storage import LocalStorageBackend
from akwb.workspace import WorkspaceBootstrap


def test_bootstrap_creates_workspace(temp_project: Path) -> None:
    config = Config()
    bus = InMemoryEventBus()
    obs = LoggerObservability(level="ERROR")
    storage = LocalStorageBackend(temp_project / config.workspace_dir, event_bus=bus)
    bootstrap = WorkspaceBootstrap(config, storage, bus, obs)

    result = bootstrap.init(temp_project)
    assert result.ok is True
    assert result.value is not None
    assert (temp_project / ".akwb" / "workspace.json").exists()


def test_bootstrap_refuses_existing_workspace(temp_project: Path) -> None:
    config = Config()
    bus = InMemoryEventBus()
    obs = LoggerObservability(level="ERROR")
    storage = LocalStorageBackend(temp_project / config.workspace_dir, event_bus=bus)
    bootstrap = WorkspaceBootstrap(config, storage, bus, obs)

    bootstrap.init(temp_project)
    result = bootstrap.init(temp_project)
    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "workspace_exists"


def test_bootstrap_force_overwrites(temp_project: Path) -> None:
    config = Config()
    bus = InMemoryEventBus()
    obs = LoggerObservability(level="ERROR")
    storage = LocalStorageBackend(temp_project / config.workspace_dir, event_bus=bus)
    bootstrap = WorkspaceBootstrap(config, storage, bus, obs)

    bootstrap.init(temp_project)
    result = bootstrap.init(temp_project, force=True)
    assert result.ok is True
