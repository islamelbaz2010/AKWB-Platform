"""Tests for the plugin loader and registry."""

from pathlib import Path

from akwb.plugins import PluginRegistry


def test_manifest_loader(sample_plugin_dir: Path) -> None:
    from akwb.plugins.manifest import ManifestLoader

    result = ManifestLoader.load(sample_plugin_dir)
    assert result.ok is True
    assert result.value is not None
    assert result.value.name == "sample"
    assert result.value.plugin_api_version == "1"


def test_load_sample_plugin(sample_plugin_dir: Path) -> None:
    registry = PluginRegistry()
    result = registry.load_from_directory(sample_plugin_dir)
    assert result.ok is True
    assert result.value.manifest.name == "sample"
    assert len(registry.list_plugins()) == 1


def test_unsupported_api_version(tmp_path: Path) -> None:
    import yaml

    plugin_dir = tmp_path / "bad_plugin"
    plugin_dir.mkdir()
    manifest = {
        "name": "bad",
        "version": "1.0.0",
        "plugin_api_version": "99",
        "entry_point": "plugin.py",
    }
    with (plugin_dir / "plugin.yaml").open("w") as f:
        yaml.safe_dump(manifest, f)

    registry = PluginRegistry()
    result = registry.load_from_directory(plugin_dir)
    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "plugin_api_version"
