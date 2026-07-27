"""Artifact registry and entry models used by the Discovery engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from akwb.types import utc_now

if TYPE_CHECKING:
    from akwb.domain.ports import StoragePort


class ArtifactEntry(BaseModel):
    """A single discovered project artifact."""

    model_config = ConfigDict(extra="ignore")

    id: str
    absolute_path: str
    relative_path: str
    type: str
    category: str
    extension: str
    hash: str | None
    size: int
    created_time: str
    modified_time: str
    parent_directory: str
    tags: list[str] = Field(default_factory=list)
    status: str = "discovered"
    previous_path: str | None = None


class ArtifactRegistry(BaseModel):
    """Canonical inventory of discovered artifacts for a project."""

    model_config = ConfigDict(extra="ignore")

    project_root: str
    generated_at: str = Field(default_factory=utc_now)
    artifacts: list[ArtifactEntry] = Field(default_factory=list)

    _by_path: dict[str, ArtifactEntry] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: object, /) -> None:
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._by_path = {a.relative_path: a for a in self.artifacts}

    def add(self, artifact: ArtifactEntry) -> None:
        """Add an artifact to the registry and rebuild the path index."""
        self.artifacts.append(artifact)
        self._by_path[artifact.relative_path] = artifact

    def by_path(self, relative_path: str) -> ArtifactEntry | None:
        return self._by_path.get(relative_path)

    def all(self) -> list[ArtifactEntry]:
        return list(self.artifacts)

    def save(self, storage: StoragePort, filename: str | None = None) -> None:
        """Persist the registry as JSON using a StoragePort implementation."""
        storage.write_json(filename or "artifacts.json", self.model_dump())

    @classmethod
    def load(
        cls,
        storage: StoragePort,
        filename: str | None = None,
        project_root: str | None = None,
    ) -> ArtifactRegistry:
        """Load a persisted registry or return an empty one if it does not exist."""
        name = filename or "artifacts.json"
        if not storage.exists(name):
            inferred_root = (
                project_root
                if project_root is not None
                else str(storage.root().parent)
            )
            return cls(project_root=inferred_root)
        data = storage.read_json(name)
        return cls.model_validate(data)
