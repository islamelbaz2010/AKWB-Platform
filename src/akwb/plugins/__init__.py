"""Plugin framework: manifest, loader, and registry."""

from akwb.plugins.loader import LoadedPlugin, PluginLoader
from akwb.plugins.manifest import PluginManifest
from akwb.plugins.registry import PluginAPI, PluginRegistry

__all__ = ["LoadedPlugin", "PluginAPI", "PluginLoader", "PluginManifest", "PluginRegistry"]
