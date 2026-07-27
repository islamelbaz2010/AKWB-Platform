"""Unit of Work coordinates storage operations during an AKWB command."""

from __future__ import annotations

from typing import Any

from akwb.domain.models import Artifact, WorkspaceManifest
from akwb.domain.ports import StoragePort


class UnitOfWork:
    """Stage artifacts and commit the workspace manifest atomically."""

    def __init__(self, storage: StoragePort) -> None:
        self._storage = storage
        self._staged_artifacts: list[Artifact] = []
        self._pending_manifest: dict[str, Any] | None = None

    def stage_artifact(self, artifact: Artifact) -> None:
        """Register an artifact that will appear in the next manifest."""
        self._staged_artifacts.append(artifact)

    def commit(self, manifest: WorkspaceManifest) -> None:
        """Persist the workspace manifest and clear the staging area."""
        manifest.artifacts = list(self._staged_artifacts)
        self._storage.write_json("workspace.json", manifest.to_dict())
        self._pending_manifest = None

    def get_staged_artifacts(self) -> list[Artifact]:
        """Return artifacts staged for the next commit."""
        return list(self._staged_artifacts)

    def rollback(self) -> None:
        """Discard staged artifacts without writing anything."""
        self._staged_artifacts.clear()
        self._pending_manifest = None
