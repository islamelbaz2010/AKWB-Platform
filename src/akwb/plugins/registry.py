"""Plugin registry and port resolution."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from akwb.domain.ports import Observability
from akwb.plugins.loader import LoadedPlugin, PluginLoader
from akwb.plugins.manifest import PluginManifest
from akwb.types import Diagnostic, Result


class PluginAPI:
    """Surface passed to a plugin's ``register`` function."""

    def __init__(self, registry: PluginRegistry, plugin: LoadedPlugin) -> None:
        self._registry = registry
        self._plugin = plugin

    def get_manifest(self) -> PluginManifest:
        """Return the current plugin manifest."""
        return self._plugin.manifest

    def register_port(self, port_name: str, implementation: Any) -> None:
        """Register an implementation for a named plugin port."""
        self._registry.register_port(port_name, implementation, self._plugin.manifest.name)


class PluginRegistry:
    """Collect, validate, and resolve plugins and their ports."""

    def __init__(
        self,
        loader: PluginLoader | None = None,
        observability: Observability | None = None,
    ) -> None:
        self._loader = loader or PluginLoader()
        self._observability = observability
        self._plugins: list[LoadedPlugin] = []
        self._ports: dict[str, list[Any]] = defaultdict(list)

    def load_from_directory(self, plugin_dir: Path) -> Result[LoadedPlugin, Diagnostic]:
        """Load a plugin from ``plugin_dir`` and register its ports."""
        result = self._loader.load(plugin_dir)
        if not result.ok:
            if self._observability and result.error is not None:
                self._observability.diagnostic(result.error)
            return result

        assert result.value is not None
        plugin = result.value
        self._plugins.append(plugin)

        api = PluginAPI(self, plugin)
        if plugin.register is not None:
            try:
                plugin.register(api)
            except Exception as exc:  # noqa: BLE001
                diag = Diagnostic(
                    "error",
                    "plugin_register_failed",
                    f"Plugin {plugin.manifest.name} register() failed: {exc}",
                )
                if self._observability:
                    self._observability.diagnostic(diag)
                return Result.failure(diag)

        if self._observability:
            self._observability.info(
                f"Loaded plugin {plugin.manifest.name} v{plugin.manifest.version} "
                f"with ports {plugin.manifest.ports}"
            )

        return Result.success(plugin)

    def register_port(
        self,
        port_name: str,
        implementation: Any,
        plugin_name: str | None = None,
    ) -> None:
        """Register an implementation for a plugin port."""
        if not isinstance(implementation, type) and not hasattr(implementation, "port_name"):
            raise TypeError(
                f"Plugin port implementation must be a class or object with port_name: {implementation}"
            )
        self._ports[port_name].append(implementation)

    def resolve(self, port_name: str) -> list[Any]:
        """Return all implementations registered for ``port_name``."""
        return list(self._ports.get(port_name, []))

    def list_plugins(self) -> list[LoadedPlugin]:
        """Return all loaded plugins."""
        return list(self._plugins)

    def load_all(self, plugin_dirs: list[str]) -> list[Result[LoadedPlugin, Diagnostic]]:
        """Load plugins from every directory in ``plugin_dirs``."""
        results: list[Result[LoadedPlugin, Diagnostic]] = []
        for raw in plugin_dirs:
            path = Path(raw).expanduser().resolve()
            if path.is_dir():
                for sub in sorted(path.iterdir()):
                    if sub.is_dir() and (sub / "plugin.yaml").exists():
                        results.append(self.load_from_directory(sub))
            elif path.exists():
                results.append(self.load_from_directory(path))
        return results
