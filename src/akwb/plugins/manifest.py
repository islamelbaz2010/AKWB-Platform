"""Plugin manifest schema and validation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from akwb.types import Diagnostic, Result


class PluginManifest(BaseModel):
    """A validated plugin.yaml descriptor."""

    model_config = ConfigDict(extra="ignore")

    name: str
    version: str
    plugin_api_version: str
    description: str = ""
    entry_point: str
    ports: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=lambda: ["filesystem:read"])


class ManifestLoader:
    """Load plugin manifests from the filesystem."""

    @staticmethod
    def load(plugin_dir: Path) -> Result[PluginManifest, Diagnostic]:
        for filename in ("plugin.yaml", "plugin.yml"):
            candidate = plugin_dir / filename
            if candidate.exists():
                try:
                    with candidate.open("r", encoding="utf-8") as f:
                        raw = yaml.safe_load(f)
                    if not isinstance(raw, dict):
                        return Result.failure(
                            Diagnostic(
                                "error",
                                "manifest_format",
                                f"Plugin manifest {candidate} is not a mapping",
                            )
                        )
                    return Result.success(PluginManifest.model_validate(raw))
                except (OSError, yaml.YAMLError, ValueError, TypeError, ValidationError) as exc:
                    return Result.failure(
                        Diagnostic(
                            "error",
                            "manifest_load",
                            f"Failed to load {candidate}: {exc}",
                        )
                    )
        return Result.failure(
            Diagnostic(
                "error",
                "manifest_missing",
                f"No plugin.yaml found in {plugin_dir}",
            )
        )
