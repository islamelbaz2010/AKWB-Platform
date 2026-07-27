"""Integration tests for the AKWB CLI."""

import json
from pathlib import Path

from click.testing import CliRunner

from akwb.cli import cli


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "1.0.0" in result.output


def test_init_and_doctor() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        project = Path("project")
        project.mkdir()

        init_result = runner.invoke(cli, ["--project-root", str(project), "init"])
        assert init_result.exit_code == 0, init_result.output

        doctor_result = runner.invoke(cli, ["--project-root", str(project), "doctor"])
        assert doctor_result.exit_code == 0, doctor_result.output


def test_init_json_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        project = Path("project")
        project.mkdir()

        result = runner.invoke(cli, ["--project-root", str(project), "init", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["ok"] is True
        assert ".akwb" in data["workspace_dir"]


def test_doctor_json_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        project = Path("project")
        project.mkdir()

        runner.invoke(cli, ["--project-root", str(project), "init"])
        result = runner.invoke(cli, ["--project-root", str(project), "doctor", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "diagnostics" in data
