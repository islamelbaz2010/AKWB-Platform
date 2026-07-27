"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest
import yaml

from akwb.config import Config, ConfigLoader


def test_default_config() -> None:
    c = Config()
    assert c.log_level == "INFO"
    assert c.workspace_dir == ".akwb"
    assert c.telemetry_enabled is False
    assert c.storage.backend == "local"


def test_config_from_project_file(temp_project: Path) -> None:
    with (temp_project / "akwb.yaml").open("w") as f:
        yaml.safe_dump({"log_level": "DEBUG", "workspace_dir": ".akwb2"}, f)

    loader = ConfigLoader(global_config_path=Path("/nonexistent"))
    c = loader.load(temp_project)
    assert c.log_level == "DEBUG"
    assert c.workspace_dir == ".akwb2"


def test_env_override(monkeypatch) -> None:
    monkeypatch.setenv("AKWB_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AKWB_TELEMETRY_ENABLED", "true")
    monkeypatch.setenv("AKWB_STORAGE__CACHE_DIR", "/tmp/cache")

    loader = ConfigLoader(global_config_path=Path("/nonexistent"))
    c = loader.load(Path("/tmp"))
    assert c.log_level == "DEBUG"
    assert c.telemetry_enabled is True
    assert c.storage.cache_dir == "/tmp/cache"


def test_invalid_log_level_raises() -> None:
    with pytest.raises(ValueError, match="validation error"):
        Config(log_level="")  # too short, not in allowed set will be tested later
