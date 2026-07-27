"""Integration tests for the akwb discover CLI."""

import json
from pathlib import Path

from click.testing import CliRunner

from akwb.cli import cli


def test_discover_small_project_json() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        project = Path("project")
        project.mkdir()
        (project / "README.md").write_text("# test")
        (project / "src" / "main.py").parent.mkdir(parents=True)
        (project / "src" / "main.py").write_text("print(1)")
        (project / "node_modules" / "x" / "index.js").parent.mkdir(parents=True)
        (project / "node_modules" / "x" / "index.js").write_text("x")

        result = runner.invoke(cli, ["--project-root", str(project), "discover", "--json"])
        assert result.exit_code == 0, result.output

        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["artifact_count"] == 3
        relative_paths = {a["relative_path"] for a in data["artifacts"]}
        assert "src" in relative_paths
        assert "README.md" in relative_paths
        assert "src/main.py" in relative_paths
        assert "node_modules/x/index.js" not in relative_paths


def test_discover_respects_user_ignore() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        project = Path("project")
        project.mkdir()
        (project / ".akwbignore").write_text("*.secret\n")
        (project / "public.txt").write_text("x")
        (project / "hidden.secret").write_text("x")

        result = runner.invoke(cli, ["--project-root", str(project), "discover", "--json"])
        assert result.exit_code == 0, result.output

        data = json.loads(result.output)
        relative_paths = {a["relative_path"] for a in data["artifacts"]}
        assert "public.txt" in relative_paths
        assert "hidden.secret" not in relative_paths


def test_discover_empty_project() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        project = Path("project")
        project.mkdir()

        result = runner.invoke(cli, ["--project-root", str(project), "discover", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["artifact_count"] == 0
