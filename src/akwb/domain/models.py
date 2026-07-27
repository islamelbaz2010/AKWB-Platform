"""Core domain models and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from akwb._version import VERSION
from akwb.types import utc_now


@dataclass(frozen=True)
class Artifact:
    """A generated artifact inside the workspace."""

    name: str
    relative_path: str
    mime_type: str
    schema_version: str | None = None


@dataclass(frozen=True)
class Project:
    """A project root known to AKWB."""

    name: str
    root: Path


@dataclass
class WorkspaceManifest:
    """The canonical description of an AKWB workspace."""

    schema_version: str = "workspace-v1"
    akwb_version: str = field(default=VERSION)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    project_root: str | None = None
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Artifact] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "akwb_version": self.akwb_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_root": self.project_root,
            "config_snapshot": self.config_snapshot,
            "artifacts": [
                {
                    "name": a.name,
                    "relative_path": a.relative_path,
                    "mime_type": a.mime_type,
                    "schema_version": a.schema_version,
                }
                for a in self.artifacts
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkspaceManifest:
        artifacts = [
            Artifact(
                name=a["name"],
                relative_path=a["relative_path"],
                mime_type=a["mime_type"],
                schema_version=a.get("schema_version"),
            )
            for a in data.get("artifacts", [])
        ]
        return cls(
            schema_version=data.get("schema_version", "workspace-v1"),
            akwb_version=data.get("akwb_version", VERSION),
            created_at=data.get("created_at", utc_now()),
            updated_at=utc_now(),
            project_root=data.get("project_root"),
            config_snapshot=data.get("config_snapshot", {}),
            artifacts=artifacts,
        )
