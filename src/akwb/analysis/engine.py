"""Analyze engine that orchestrates discovery, extraction, graph building,
persistence, and reporting for Sprint 7.
"""

from __future__ import annotations

import dataclasses
import json
import mimetypes
from pathlib import Path
from typing import Any

from akwb._version import VERSION
from akwb.container import Container
from akwb.discovery.models import ArtifactEntry, ArtifactRegistry
from akwb.domain.models import Artifact, WorkspaceManifest
from akwb.extraction.pipeline import ExtractionPipeline
from akwb.extraction.python import PythonSourceParser
from akwb.graph.models import GraphStatisticsResult, KnowledgeGraph
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeConfidence,
    KnowledgeEvidence,
    KnowledgeMetadata,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
    ReferenceKind,
)
from akwb.types import Diagnostic, Result, utc_now


@dataclasses.dataclass
class AnalyzeResult:
    """Result of running ``akwb analyze`` on a project."""

    ok: bool
    workspace_dir: Path
    artifact_count: int
    object_count: int
    relationship_count: int
    graph_density: float
    diagnostics: list[Diagnostic]
    error: Diagnostic | None = None


class AnalyzeEngine:
    """Coordinate the end-to-end AKWB analysis flow."""

    def __init__(self, container: Container) -> None:
        self.container = container

    def analyze(
        self,
        project_root: Path,
        force: bool = False,
        depth: str = "standard",
    ) -> AnalyzeResult:
        """Run the full AKWB analysis pipeline and persist the workspace."""
        project_root = project_root.resolve()
        diagnostics: list[Diagnostic] = []

        # 1. Load plugins before any engine work.
        self.container.load_plugins()

        # 2. Ensure workspace exists.
        workspace_dir = project_root / self.container.config.workspace_dir
        if not workspace_dir.exists() or force:
            init_result = self.container.workspace_bootstrap.init(project_root, force=force)
            if not init_result.ok:
                return AnalyzeResult(
                    ok=False,
                    workspace_dir=workspace_dir,
                    artifact_count=0,
                    object_count=0,
                    relationship_count=0,
                    graph_density=0.0,
                    diagnostics=init_result.diagnostics,
                    error=init_result.error,
                )

        # 3. Discovery.
        discovery_result = self.container.discovery_engine.discover(project_root)
        if not discovery_result.ok or discovery_result.value is None:
            return AnalyzeResult(
                ok=False,
                workspace_dir=workspace_dir,
                artifact_count=0,
                object_count=0,
                relationship_count=0,
                graph_density=0.0,
                diagnostics=discovery_result.diagnostics,
                error=discovery_result.error,
            )
        registry = discovery_result.value
        diagnostics.extend(discovery_result.diagnostics)

        # 4. Initialize catalog.
        framework = self.container.knowledge_framework
        catalog = framework.new_catalog(
            project_id=project_root.name,
            project_root=str(project_root),
            akwb_version=VERSION,
            depth=depth,
        )

        file_object_map: dict[str, KnowledgeObject] = {}
        python_imports: list[tuple[str, str]] = []
        python_import_sources: dict[str, KnowledgeObject] = {}
        artifact_count = len(registry.artifacts)
        processed = 0

        for entry in sorted(registry.artifacts, key=lambda a: a.relative_path):
            if entry.type == "directory":
                continue

            rel = entry.relative_path
            file_obj = self._file_object_for(entry, project_root)
            if file_obj is None:
                diagnostics.append(
                    Diagnostic(
                        "info",
                        "skipped_artifact",
                        f"Skipped {rel}: unsupported category {entry.category!r}",
                        source_ref=rel,
                    )
                )
                continue

            file_path = project_root / rel
            if not file_path.is_file():
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "missing_artifact_file",
                        f"Artifact file not found: {rel}",
                        source_ref=rel,
                    )
                )
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "read_failed",
                        f"Could not read {rel}: {exc}",
                        source_ref=rel,
                    )
                )
                continue

            if Path(rel).suffix == ".py":
                parser = PythonSourceParser(
                    parent=file_obj,
                    source=file_obj.sources[0],
                    project_root=project_root,
                    relative_path=rel,
                )
                try:
                    py_result = parser.parse(content)
                except (SyntaxError, ValueError) as exc:
                    diagnostics.append(
                        Diagnostic(
                            "warning",
                            "python_parse_failed",
                            f"Could not parse {rel}: {exc}",
                            source_ref=rel,
                        )
                    )
                    continue
                if py_result.objects or py_result.import_targets:
                    catalog.add_object(file_obj)
                    file_object_map[rel] = file_obj
                    for obj in py_result.objects:
                        catalog.add_object(obj)
                        catalog.add_relationship(
                            self._contains_relationship(file_obj, obj)
                        )
                    for target in py_result.import_targets:
                        python_imports.append((file_obj.id, target))
                        python_import_sources[file_obj.id] = file_obj
                processed += 1
                continue

            pipeline_result = self._run_pipeline(
                entry,
                content,
                self.container.extraction_pipeline,
                project_root.name,
            )
            diagnostics.extend(pipeline_result.diagnostics)

            if pipeline_result.value:
                catalog.add_object(file_obj)
                file_object_map[rel] = file_obj
                for obj in pipeline_result.value:
                    catalog.add_object(obj)
                    catalog.add_relationship(
                        self._contains_relationship(file_obj, obj)
                    )
            processed += 1

        # 5. Resolve Python import relationships.
        for source_id, target_rel in python_imports:
            if target_rel in file_object_map:
                target_obj = file_object_map[target_rel]
                source_obj = python_import_sources.get(source_id, target_obj)
                catalog.add_relationship(
                    KnowledgeRelationship(
                        relationship_type="depends_on",
                        from_ref=KnowledgeReference(
                            ref=source_id,
                            kind=ReferenceKind.KNOWLEDGE_OBJECT,
                        ),
                        to_ref=KnowledgeReference(
                            ref=target_obj.id,
                            kind=ReferenceKind.KNOWLEDGE_OBJECT,
                        ),
                        evidence=[
                            KnowledgeEvidence(
                                source=source_obj.sources[0] if source_obj.sources else target_obj.sources[0],
                                type="extraction",
                                excerpt="import",
                            )
                        ],
                    )
                )

        # 6. Build, validate, and measure graph.
        try:
            graph = self.container.graph_engine.build(catalog)
        except Exception as exc:  # noqa: BLE001
            diag = Diagnostic(
                "error",
                "graph_build_failed",
                f"Failed to build knowledge graph: {exc}",
            )
            diagnostics.append(diag)
            return AnalyzeResult(
                ok=False,
                workspace_dir=workspace_dir,
                artifact_count=artifact_count,
                object_count=0,
                relationship_count=0,
                graph_density=0.0,
                diagnostics=diagnostics,
                error=diag,
            )

        graph_validation = self.container.graph_engine.validate(graph)
        diagnostics.extend(graph_validation.diagnostics)

        stats = self.container.graph_engine.statistics(graph)

        # 7. Persist workspace artifacts.
        try:
            self._persist_workspace(
                registry,
                catalog,
                graph,
                stats,
                diagnostics,
                project_root,
                workspace_dir,
            )
        except Exception as exc:  # noqa: BLE001
            diag = Diagnostic(
                "error",
                "persist_workspace_failed",
                f"Failed to persist workspace: {exc}",
            )
            diagnostics.append(diag)
            return AnalyzeResult(
                ok=False,
                workspace_dir=workspace_dir,
                artifact_count=artifact_count,
                object_count=catalog.object_count(),
                relationship_count=catalog.relationship_count(),
                graph_density=stats.density,
                diagnostics=diagnostics,
                error=diag,
            )

        has_errors = any(d.level == "error" for d in diagnostics)
        return AnalyzeResult(
            ok=not has_errors,
            workspace_dir=workspace_dir,
            artifact_count=artifact_count,
            object_count=catalog.object_count(),
            relationship_count=catalog.relationship_count(),
            graph_density=stats.density,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _run_pipeline(
        entry: ArtifactEntry,
        content: str,
        pipeline: ExtractionPipeline,
        project_id: str,
    ) -> Result[list[Any], Diagnostic]:
        """Run the extraction pipeline on a non-Python artifact."""
        mime_type = mimetypes.guess_type(Path(entry.relative_path).name)[0] or "text/plain"
        artifact = Artifact(
            name=Path(entry.relative_path).name,
            relative_path=entry.relative_path,
            mime_type=mime_type,
        )
        result = pipeline.extract(artifact, content, project_id=project_id)
        return Result(
            ok=result.ok,
            value=result.objects,
            diagnostics=result.diagnostics,
        )

    def _file_object_for(
        self,
        entry: ArtifactEntry,
        project_root: Path,
    ) -> KnowledgeObject | None:
        """Return a knowledge object representing a source file, or None to skip."""
        rel = entry.relative_path
        suffix = Path(rel).suffix
        mime_type = mimetypes.guess_type(Path(rel).name)[0] or "text/plain"

        if entry.category in ("media", "archive"):
            return None
        if entry.type in ("pdf", "docx", "pptx"):
            return None

        if suffix == ".py" or entry.type == "source_code":
            file_type = "component"
            source_kind = "code"
        elif entry.type in ("markdown", "text") or suffix in (".md", ".txt", ".rst"):
            file_type = "document"
            source_kind = "markdown" if entry.type == "markdown" else "text"
        else:
            file_type = "document"
            source_kind = "manual"

        source = KnowledgeSource(
            kind=source_kind,
            uri=rel,
            mime_type=mime_type,
        )
        evidence = KnowledgeEvidence(
            source=source,
            type="extraction",
            excerpt=rel,
            extracted_by="akwb.analysis",
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
        )

        title = rel
        if suffix == ".py":
            title = Path(rel).with_suffix("").as_posix().replace("/", ".")

        return KnowledgeObject(
            id=f"ku://file/{rel}",
            type=file_type,
            title=title,
            description=rel,
            content=None,
            sources=[source],
            evidence=[evidence],
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
            metadata=KnowledgeMetadata(
                project_id=project_root.name,
                custom={"relative_path": rel, "category": entry.category},
            ),
        )

    @staticmethod
    def _contains_relationship(
        source: KnowledgeObject,
        target: KnowledgeObject,
    ) -> KnowledgeRelationship:
        return KnowledgeRelationship(
            relationship_type="contains",
            from_ref=KnowledgeReference(
                ref=source.id,
                kind=ReferenceKind.KNOWLEDGE_OBJECT,
            ),
            to_ref=KnowledgeReference(
                ref=target.id,
                kind=ReferenceKind.KNOWLEDGE_OBJECT,
            ),
            evidence=[
                KnowledgeEvidence(
                    source=source.sources[0] if source.sources else target.sources[0],
                    type="extraction",
                    excerpt=f"{source.title} contains {target.title}",
                )
            ],
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
        )

    def _persist_workspace(
        self,
        registry: ArtifactRegistry,
        catalog: KnowledgeCatalog,
        graph: KnowledgeGraph,
        stats: GraphStatisticsResult,
        diagnostics: list[Diagnostic],
        project_root: Path,
        workspace_dir: Path,
    ) -> None:
        storage = self.container.storage

        # Source catalog (JSONL).
        storage.ensure_dir("index")
        source_lines = [
            json.dumps(
                {"kind": "ArtifactEntry", "data": entry.model_dump(mode="json")},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            for entry in registry.artifacts
        ]
        storage.write_text(
            "index/source_catalog.jsonl",
            "\n".join(source_lines) + "\n" if source_lines else "",
        )

        # Knowledge catalog.
        storage.ensure_dir("knowledge")
        catalog_jsonl = self.container.knowledge_framework.serialize_catalog(catalog, "jsonl")
        storage.write_text("knowledge/catalog.jsonl", catalog_jsonl)

        # Graph artifacts (graph/ and knowledge/).
        storage.ensure_dir("graph")
        graph_save = self.container.graph_engine.save(graph, "graph")
        if not graph_save.ok:
            raise RuntimeError(f"Graph save failed: {graph_save.error}")

        knowledge_graph_save = self.container.graph_engine.save(graph, "knowledge")
        if not knowledge_graph_save.ok:
            raise RuntimeError(f"Knowledge graph save failed: {knowledge_graph_save.error}")

        # Reports.
        storage.ensure_dir("reports")
        summary = {
            "ok": not any(d.level == "error" for d in diagnostics),
            "project_root": str(project_root),
            "artifact_count": len(registry.artifacts),
            "object_count": catalog.object_count(),
            "relationship_count": catalog.relationship_count(),
            "graph_density": stats.density,
            "node_type_counts": stats.node_type_counts,
            "edge_type_counts": stats.edge_type_counts,
            "diagnostics": [
                {
                    "level": d.level,
                    "code": d.code,
                    "message": d.message,
                    "source_ref": d.source_ref,
                }
                for d in diagnostics
            ],
        }
        storage.write_json("reports/summary.json", summary)

        summary_md_lines = [
            "# AKWB Analysis Summary",
            "",
            f"- Project: {project_root.name}",
            f"- Project root: {project_root}",
            f"- Artifacts analyzed: {summary['artifact_count']}",
            f"- Knowledge objects: {summary['object_count']}",
            f"- Knowledge relationships: {summary['relationship_count']}",
            f"- Graph density: {stats.density:.4f}",
        ]
        if stats.node_type_counts:
            summary_md_lines.append("")
            summary_md_lines.append("## Node types")
            for node_type, count in sorted(stats.node_type_counts.items()):
                summary_md_lines.append(f"- {node_type}: {count}")
        if stats.edge_type_counts:
            summary_md_lines.append("")
            summary_md_lines.append("## Edge types")
            for edge_type, count in sorted(stats.edge_type_counts.items()):
                summary_md_lines.append(f"- {edge_type}: {count}")
        storage.write_text("reports/summary.md", "\n".join(summary_md_lines) + "\n")

        # Log.
        storage.ensure_dir("logs")
        log_lines = ["AKWB Analysis Log", ""]
        for d in diagnostics:
            log_lines.append(f"[{d.level.upper()}:{d.code}] {d.message}")
            if d.source_ref:
                log_lines.append(f"  source: {d.source_ref}")
        storage.write_text("logs/analysis.log", "\n".join(log_lines) + "\n")

        # Update workspace manifest.
        manifest_data = storage.read_json("workspace.json")
        manifest = WorkspaceManifest.from_dict(manifest_data)
        manifest.updated_at = utc_now()
        manifest.artifacts = [
            Artifact(name="source_catalog.jsonl", relative_path="index/source_catalog.jsonl", mime_type="application/jsonl"),
            Artifact(name="catalog.jsonl", relative_path="knowledge/catalog.jsonl", mime_type="application/jsonl"),
            Artifact(name="graph.jsonl", relative_path="graph/graph.jsonl", mime_type="application/jsonl"),
            Artifact(name="graph_nodes.jsonl", relative_path="graph/graph_nodes.jsonl", mime_type="application/jsonl"),
            Artifact(name="graph_edges.jsonl", relative_path="graph/graph_edges.jsonl", mime_type="application/jsonl"),
            Artifact(name="graph.dot", relative_path="graph/graph.dot", mime_type="text/vnd.graphviz"),
            Artifact(name="graph.cypher", relative_path="graph/graph.cypher", mime_type="text/plain"),
            Artifact(name="summary.md", relative_path="reports/summary.md", mime_type="text/markdown"),
            Artifact(name="summary.json", relative_path="reports/summary.json", mime_type="application/json"),
            Artifact(name="analysis.log", relative_path="logs/analysis.log", mime_type="text/plain"),
        ]
        storage.write_json("workspace.json", manifest.to_dict())
