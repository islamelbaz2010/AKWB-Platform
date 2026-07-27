"""AKWB CLI entry point and commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from akwb import __version__
from akwb.analysis import AnalyzeEngine
from akwb.config import Config, ConfigLoader
from akwb.container import Container
from akwb.types import Diagnostic


def _diagnostic_to_dict(diag: Diagnostic) -> dict[str, Any]:
    return {
        "level": diag.level,
        "code": diag.code,
        "message": diag.message,
        "source_ref": diag.source_ref,
    }


def _artifact_to_dict(artifact: Any) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "absolute_path": artifact.absolute_path,
        "relative_path": artifact.relative_path,
        "type": artifact.type,
        "category": artifact.category,
        "extension": artifact.extension,
        "hash": artifact.hash,
        "size": artifact.size,
        "created_time": artifact.created_time,
        "modified_time": artifact.modified_time,
        "parent_directory": artifact.parent_directory,
        "tags": artifact.tags,
        "status": artifact.status,
        "previous_path": artifact.previous_path,
    }


@click.group()
@click.version_option(version=__version__, prog_name="akwb")
@click.option(
    "--project-root",
    "-p",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=False,
        allow_dash=False,
        path_type=Path,
    ),
    default=".",
    help="Project root directory (default: current directory).",
)
@click.pass_context
def cli(ctx: click.Context, project_root: Path) -> None:
    """AKWB — local-first knowledge workspace."""
    ctx.ensure_object(dict)
    ctx.obj["project_root"] = project_root


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Print the AKWB version."""
    click.echo(__version__)


@cli.command()
@click.argument(
    "path",
    required=False,
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=False,
        allow_dash=False,
        path_type=Path,
    ),
)
@click.option("--force", is_flag=True, help="Overwrite an existing workspace.")
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@click.pass_context
def init(
    ctx: click.Context,
    path: Path | None,
    force: bool,
    json_output: bool,
) -> None:
    """Initialize an AKWB workspace in the project root."""
    project_root = (path if path else ctx.obj["project_root"]).resolve()

    if not project_root.exists():
        click.echo(f"Project root does not exist: {project_root}", err=True)
        sys.exit(1)

    try:
        config = ConfigLoader().load(project_root)
    except Exception as exc:  # noqa: BLE001
        config = Config()
        click.echo(
            f"Warning: could not load project configuration; using defaults: {exc}",
            err=True,
        )

    container = Container(project_root, config)
    result = container.workspace_bootstrap.init(project_root, force=force)

    workspace_dir = project_root / config.workspace_dir
    output = {
        "ok": result.ok,
        "workspace_dir": str(workspace_dir),
        "diagnostics": [_diagnostic_to_dict(d) for d in result.diagnostics],
    }
    if not result.ok and result.error:
        output["error"] = str(result.error)

    if json_output:
        click.echo(json.dumps(output, indent=2))
    else:
        if result.ok:
            click.echo(f"Workspace initialized at {output['workspace_dir']}")
        else:
            click.echo(f"Failed: {output.get('error')}", err=True)

    sys.exit(0 if result.ok else 1)


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@click.pass_context
def doctor(ctx: click.Context, json_output: bool) -> None:
    """Validate the environment and workspace."""
    project_root = ctx.obj["project_root"].resolve()
    diagnostics: list[Diagnostic] = []
    ok = True

    # Python version
    diagnostics.append(
        Diagnostic(
            "info",
            "python_version",
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )

    # Project root
    if not project_root.exists():
        ok = False
        diagnostics.append(
            Diagnostic("error", "project_root", f"Project root does not exist: {project_root}")
        )
    elif not project_root.is_dir():
        ok = False
        diagnostics.append(
            Diagnostic("error", "project_root", f"Project root is not a directory: {project_root}")
        )
    else:
        try:
            probe = project_root / ".akwb-doctor-write-test"
            probe.write_text("ok")
            probe.unlink()
            diagnostics.append(
                Diagnostic("info", "project_root", f"Project root is writable: {project_root}")
            )
        except Exception as exc:  # noqa: BLE001
            ok = False
            diagnostics.append(
                Diagnostic("error", "project_root", f"Project root is not writable: {exc}")
            )

    container: Container | None = None
    try:
        container = Container(project_root)
    except Exception as exc:  # noqa: BLE001
        ok = False
        diagnostics.append(
            Diagnostic("error", "container", f"Failed to build container: {exc}")
        )

    if container is not None:
        workspace_dir = project_root / container.config.workspace_dir
        if workspace_dir.exists():
            diagnostics.append(
                Diagnostic("info", "workspace", f"Workspace exists: {workspace_dir}")
            )
            if container.storage.exists("workspace.json"):
                diagnostics.append(
                    Diagnostic("info", "storage", "workspace.json is readable")
                )
            else:
                diagnostics.append(
                    Diagnostic("warning", "storage", "workspace.json not found")
                )
        else:
            diagnostics.append(
                Diagnostic("warning", "workspace", f"Workspace not initialized: {workspace_dir}")
            )

        for plugin_dir in container.config.plugins.directories:
            path = Path(plugin_dir).expanduser().resolve()
            if path.exists():
                diagnostics.append(
                    Diagnostic("info", "plugin_dir", f"Plugin directory exists: {plugin_dir}")
                )
            else:
                diagnostics.append(
                    Diagnostic("warning", "plugin_dir", f"Plugin directory missing: {plugin_dir}")
                )

    output = {
        "ok": ok,
        "project_root": str(project_root),
        "diagnostics": [_diagnostic_to_dict(d) for d in diagnostics],
    }

    if json_output:
        click.echo(json.dumps(output, indent=2))
    else:
        for d in diagnostics:
            click.echo(f"[{d.level.upper()}:{d.code}] {d.message}")

    sys.exit(0 if ok else 1)


@cli.command()
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@click.pass_context
def discover(ctx: click.Context, json_output: bool) -> None:
    """Discover all artifacts in the project and write the artifact registry."""
    project_root = ctx.obj["project_root"].resolve()

    if not project_root.exists():
        click.echo(f"Project root does not exist: {project_root}", err=True)
        sys.exit(1)

    try:
        config = ConfigLoader().load(project_root)
    except Exception as exc:  # noqa: BLE001
        config = Config()
        click.echo(
            f"Warning: could not load project configuration; using defaults: {exc}",
            err=True,
        )

    container = Container(project_root, config)

    workspace_dir = project_root / config.workspace_dir
    if not workspace_dir.exists():
        init_result = container.workspace_bootstrap.init(project_root)
        if not init_result.ok:
            click.echo("Failed to initialize workspace.", err=True)
            sys.exit(1)

    result = container.discovery_engine.discover(project_root)

    output: dict[str, Any] = {"ok": result.ok}
    if result.ok and result.value:
        registry = result.value
        output["artifact_count"] = len(registry.artifacts)
        output["registry_path"] = str(container.storage.root() / config.discovery.registry_file)
        output["artifacts"] = [_artifact_to_dict(a) for a in registry.artifacts]
    if not result.ok and result.error:
        output["error"] = str(result.error)
    output["diagnostics"] = [_diagnostic_to_dict(d) for d in result.diagnostics]

    if json_output:
        click.echo(json.dumps(output, indent=2))
    else:
        if result.ok:
            click.echo(f"Discovered {output.get('artifact_count', 0)} artifacts")
        else:
            click.echo(f"Failed: {output.get('error')}", err=True)

    sys.exit(0 if result.ok else 1)


@cli.command()
@click.argument(
    "path",
    required=False,
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=False,
        readable=True,
        resolve_path=False,
        allow_dash=False,
        path_type=Path,
    ),
)
@click.option("--force", is_flag=True, help="Overwrite an existing workspace.")
@click.option(
    "--depth",
    default="standard",
    type=click.Choice(["minimal", "standard", "deep"], case_sensitive=False),
    help="Analysis depth (default: standard).",
)
@click.option("--json", "json_output", is_flag=True, help="Output JSON.")
@click.pass_context
def analyze(
    ctx: click.Context,
    path: Path | None,
    force: bool,
    depth: str,
    json_output: bool,
) -> None:
    """Analyze the project and produce a .akwb workspace."""
    project_root = (path if path else ctx.obj["project_root"]).resolve()

    if not project_root.exists():
        click.echo(f"Project root does not exist: {project_root}", err=True)
        sys.exit(2)
    if not project_root.is_dir():
        click.echo(f"Project root is not a directory: {project_root}", err=True)
        sys.exit(2)

    try:
        config = ConfigLoader().load(project_root)
    except Exception as exc:  # noqa: BLE001
        config = Config()
        click.echo(
            f"Warning: could not load project configuration; using defaults: {exc}",
            err=True,
        )

    container = Container(project_root, config)
    engine = AnalyzeEngine(container)
    result = engine.analyze(project_root, force=force, depth=depth)

    output = {
        "ok": result.ok,
        "project_root": str(project_root),
        "workspace_dir": str(result.workspace_dir),
        "artifact_count": result.artifact_count,
        "object_count": result.object_count,
        "relationship_count": result.relationship_count,
        "graph_density": result.graph_density,
        "diagnostics": [
            {
                "level": d.level,
                "code": d.code,
                "message": d.message,
                "source_ref": d.source_ref,
            }
            for d in result.diagnostics
        ],
    }
    if result.error:
        output["error"] = {
            "level": result.error.level,
            "code": result.error.code,
            "message": result.error.message,
            "source_ref": result.error.source_ref,
        }

    if json_output:
        click.echo(json.dumps(output, indent=2))
    else:
        if result.ok:
            click.echo(f"Analyzed {output['artifact_count']} artifacts")
            click.echo(f"Knowledge objects: {output['object_count']}")
            click.echo(f"Knowledge relationships: {output['relationship_count']}")
            click.echo(f"Workspace written to {output['workspace_dir']}")
        else:
            click.echo(f"Analysis failed: {result.error}", err=True)
        if result.diagnostics:
            click.echo("")
            for d in result.diagnostics:
                click.echo(f"[{d.level.upper()}:{d.code}] {d.message}")

    if result.ok:
        sys.exit(0)
    if result.error and result.error.code.startswith("plugin"):
        sys.exit(10)
    if result.artifact_count == 0:
        sys.exit(3)
    sys.exit(1 if result.error else 4)


@cli.command("report")
@click.argument("name", default="summary", type=click.Choice(["summary", "structure", "graph"]))
@click.option("--json", "json_output", is_flag=True, help="Output JSON when available.")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Write report to a file.")
@click.pass_context
def report(
    ctx: click.Context,
    name: str,
    json_output: bool,
    output: Path | None,
) -> None:
    """Generate a report from an analyzed workspace."""
    project_root = ctx.obj["project_root"].resolve()
    workspace_dir = project_root / ".akwb"
    if not workspace_dir.exists():
        click.echo("Workspace not found. Run 'akwb init' and 'akwb analyze' first.", err=True)
        sys.exit(1)

    container = Container(project_root)
    storage = container.storage

    try:
        if name == "summary":
            if json_output:
                text = storage.read_text("reports/summary.json")
            else:
                text = storage.read_text("reports/summary.md")
        elif name == "structure":
            data = storage.read_json("reports/summary.json")
            lines = ["# AKWB Structure Report", ""]
            for node_type, count in sorted(data.get("node_type_counts", {}).items()):
                lines.append(f"- {node_type}: {count}")
            text = "\n".join(lines) + "\n"
        else:  # graph
            text = storage.read_text("graph/graph.dot")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Failed to generate report: {exc}", err=True)
        sys.exit(1)

    if output:
        output.write_text(text, encoding="utf-8")
        click.echo(f"Report written to {output}")
    else:
        click.echo(text)

    sys.exit(0)


@cli.command("export")
@click.argument("format", type=click.Choice(["jsonl", "dot", "cypher"]))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Write export to a file.")
@click.pass_context
def export(
    ctx: click.Context,
    format: str,
    output: Path | None,
) -> None:
    """Export the knowledge graph to a portable format."""
    project_root = ctx.obj["project_root"].resolve()
    workspace_dir = project_root / ".akwb"
    if not workspace_dir.exists():
        click.echo("Workspace not found. Run 'akwb init' and 'akwb analyze' first.", err=True)
        sys.exit(1)

    container = Container(project_root)
    storage = container.storage

    path_map = {
        "jsonl": "graph/graph.jsonl",
        "dot": "graph/graph.dot",
        "cypher": "graph/graph.cypher",
    }
    try:
        text = storage.read_text(path_map[format])
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Failed to export graph: {exc}", err=True)
        sys.exit(1)

    if output:
        output.write_text(text, encoding="utf-8")
        click.echo(f"Exported to {output}")
    else:
        click.echo(text)

    sys.exit(0)


def main() -> None:
    """Console script entry point."""
    cli()
