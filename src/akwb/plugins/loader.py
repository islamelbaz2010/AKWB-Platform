"""Plugin loading and module import."""

from __future__ import annotations

import importlib.util
import sys
import types
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from akwb.plugins.manifest import ManifestLoader, PluginManifest
from akwb.types import Diagnostic, Result


@dataclass
class LoadedPlugin:
    """A successfully loaded plugin with its manifest and callable surface."""

    directory: Path
    manifest: PluginManifest
    module: types.ModuleType
    register: Callable[[Any], None] | None = None


class PluginLoader:
    """Load and validate plugin packages from the filesystem."""

    SUPPORTED_API_VERSION = "1"

    def load(self, plugin_dir: Path) -> Result[LoadedPlugin, Diagnostic]:
        """Load a plugin from ``plugin_dir`` containing ``plugin.yaml``."""
        manifest_result = ManifestLoader.load(plugin_dir)
        if not manifest_result.ok:
            assert manifest_result.error is not None
            return Result.failure(manifest_result.error)
        assert manifest_result.value is not None
        manifest = manifest_result.value

        if manifest.plugin_api_version != self.SUPPORTED_API_VERSION:
            return Result.failure(
                Diagnostic(
                    "error",
                    "plugin_api_version",
                    f"Plugin {manifest.name} requires API version {manifest.plugin_api_version}; "
                    f"supported version is {self.SUPPORTED_API_VERSION}",
                )
            )

        entry_path = plugin_dir / manifest.entry_point
        if not entry_path.exists() and entry_path.with_suffix(".py").exists():
            entry_path = entry_path.with_suffix(".py")

        if not entry_path.exists():
            return Result.failure(
                Diagnostic(
                    "error",
                    "plugin_entry_point",
                    f"Entry point {manifest.entry_point} not found in {plugin_dir}",
                )
            )

        module = self._load_module_from_file(entry_path, manifest.name)
        register: Callable[[Any], None] | None = getattr(module, "register", None)

        return Result.success(
            LoadedPlugin(
                directory=plugin_dir,
                manifest=manifest,
                module=module,
                register=register,
            )
        )

    @staticmethod
    def _load_module_from_file(path: Path, name: str) -> types.ModuleType:
        """Import a Python module from an arbitrary filesystem path."""
        spec = importlib.util.spec_from_file_location(
            f"akwb.dynamic_plugin.{name}",
            str(path),
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
