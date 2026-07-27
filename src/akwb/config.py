"""Configuration loading, merging, and validation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StorageConfig(BaseModel):
    """Storage-related configuration."""

    model_config = ConfigDict(extra="ignore")

    backend: str = "local"
    cache_dir: str = "cache"


class PluginConfig(BaseModel):
    """Plugin search and permission defaults."""

    model_config = ConfigDict(extra="ignore")

    directories: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=lambda: ["filesystem:read"])


class DiscoveryConfig(BaseModel):
    """Discovery engine tuning and ignore defaults."""

    model_config = ConfigDict(extra="ignore")

    follow_symlinks: bool = False
    hash_algorithm: str = "sha256"
    max_file_size_bytes: int | None = None
    include_directories: bool = True
    registry_file: str = "artifacts.json"
    default_ignored: list[str] = Field(
        default_factory=lambda: [
            ".git",
            "node_modules",
            "dist",
            "build",
            "coverage",
            ".next",
            ".cache",
            "vendor",
            "venv",
            ".venv",
            "target",
            "__pycache__",
            ".akwb",
        ]
    )
    ignore_patterns: list[str] = Field(default_factory=list)


class Config(BaseModel):
    """Effective AKWB configuration."""

    model_config = ConfigDict(extra="ignore")

    log_level: str = "INFO"
    workspace_dir: str = ".akwb"
    project_name: str | None = None
    telemetry_enabled: bool = False
    storage: StorageConfig = Field(default_factory=StorageConfig)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}, got {value!r}")
        return upper

    @property
    def workspace_path(self) -> str:
        return self.workspace_dir


def _coerce_env_value(raw: str) -> Any:
    """Convert common environment variable strings to typed values."""
    lowered = raw.strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw


def _set_nested(target: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set a value in a nested dict using dot-separated keys."""
    parts = dotted_key.split(".")
    current = target
    for part in parts[:-1]:
        current = current.setdefault(part, {})
        if not isinstance(current, dict):
            raise TypeError(f"Configuration key '{dotted_key}' conflicts with existing scalar")
    current[parts[-1]] = value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (later wins)."""
    result: dict[str, Any] = {}
    for key, base_value in base.items():
        if key in override:
            override_value = override[key]
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                result[key] = _deep_merge(base_value, override_value)
            else:
                result[key] = override_value
        else:
            result[key] = base_value
    for key, override_value in override.items():
        if key not in base:
            result[key] = override_value
    return result


def _read_yaml(path: Path) -> dict[str, Any] | None:
    """Read a YAML file and return a dict, or None if the file is missing/empty."""
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError(f"Configuration file {path} must contain a top-level mapping")
    return data


class ConfigLoader:
    """Load and merge configuration from defaults, files, env vars, and CLI args."""

    def __init__(self, global_config_path: Path | None = None) -> None:
        self.global_config_path = global_config_path or (
            Path.home() / ".config" / "akwb" / "config.yaml"
        )

    def _defaults(self) -> dict[str, Any]:
        return Config().model_dump()

    def _env_config(self) -> dict[str, Any]:
        """Build a nested dict from ``AKWB_*`` environment variables."""
        env: dict[str, Any] = {}
        for key, raw in os.environ.items():
            if not key.startswith("AKWB_"):
                continue
            local_key = key[5:].lower().replace("__", ".")
            value = _coerce_env_value(raw)
            _set_nested(env, local_key, value)
        return env

    def _project_config_path(self, project_root: Path) -> Path | None:
        """Locate the project-level config file if it exists."""
        candidates = [
            project_root / "akwb.yaml",
            project_root / ".akwb" / "config.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def load(
        self,
        project_root: Path,
        cli_overrides: dict[str, Any] | None = None,
    ) -> Config:
        """Return the effective configuration for ``project_root``."""
        base = self._defaults()

        global_data = _read_yaml(self.global_config_path)
        if global_data:
            base = _deep_merge(base, global_data)

        project_path = self._project_config_path(project_root)
        if project_path:
            project_data = _read_yaml(project_path)
            if project_data:
                base = _deep_merge(base, project_data)

        env_data = self._env_config()
        if env_data:
            base = _deep_merge(base, env_data)

        if cli_overrides:
            base = _deep_merge(base, cli_overrides)

        return Config.model_validate(base)
