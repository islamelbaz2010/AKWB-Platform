"""Bootstrap the project-owned ``.akwb`` workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

from akwb.config import Config
from akwb.domain.events import WorkspaceInitialized
from akwb.domain.models import WorkspaceManifest
from akwb.domain.ports import EventBus, Observability, StoragePort
from akwb.types import Diagnostic, Result


class WorkspaceBootstrap:
    """Create and initialize the AKWB workspace directory for a project."""

    def __init__(
        self,
        config: Config,
        storage: StoragePort,
        event_bus: EventBus,
        observability: Observability,
    ) -> None:
        self._config = config
        self._storage = storage
        self._event_bus = event_bus
        self._observability = observability

    def init(self, project_root: Path, force: bool = False) -> Result[WorkspaceManifest, Diagnostic]:
        """Create the workspace directory and write the initial manifest."""
        workspace_dir = project_root / self._config.workspace_dir

        if workspace_dir.exists() and not force:
            diag = Diagnostic(
                "error",
                "workspace_exists",
                f"Workspace already exists at {workspace_dir}; use --force to overwrite",
            )
            self._observability.diagnostic(diag)
            return Result.failure(diag)

        if workspace_dir.exists() and force:
            shutil.rmtree(workspace_dir)
            self._observability.info(f"Removed existing workspace: {workspace_dir}")

        for subdir in ("", "logs", "cache", "staging"):
            self._storage.ensure_dir(subdir)

        manifest = WorkspaceManifest(
            project_root=str(project_root.resolve()),
            config_snapshot=self._config.model_dump(),
        )

        self._storage.write_json("workspace.json", manifest.to_dict())
        self._observability.info(f"Workspace initialized at {workspace_dir}")

        self._event_bus.publish(
            WorkspaceInitialized(
                project_root=str(project_root.resolve()),
                workspace_dir=str(workspace_dir.resolve()),
            )
        )

        return Result.success(manifest)
