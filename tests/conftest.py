"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Return a temporary project root."""
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def sample_plugin_dir() -> Path:
    """Return the bundled sample plugin fixture path."""
    return Path(__file__).parent / "fixtures" / "sample_plugin"
