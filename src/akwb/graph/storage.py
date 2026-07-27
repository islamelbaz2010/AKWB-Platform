"""Local filesystem graph persistence for AKWB."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from akwb.domain.ports import StoragePort
from akwb.graph.models import GraphEdge, GraphNode, KnowledgeGraph
from akwb.graph.plugins import GraphStorage
from akwb.types import Diagnostic, Result


class LocalGraphStorage(GraphStorage):
    """Persist a KnowledgeGraph to the local ``.akwb`` workspace.

    Produces target-specific graph artifacts. By default the full set is:
    - ``graph.jsonl`` (combined nodes, edges, and metadata)
    - ``graph_nodes.jsonl``
    - ``graph_edges.jsonl``
    - ``graph.dot`` (GraphViz DOT)
    - ``graph.cypher`` (Neo4j Cypher)

    When the target directory is ``graph/`` the combined, DOT, and Cypher files
    are written. When the target directory is ``knowledge/`` only the node and
    edge JSONL files are written. Other target directories receive all five.
    """

    def __init__(self, storage: StoragePort) -> None:
        self._storage = storage

    def save(self, graph: KnowledgeGraph, target: Any) -> Result[bool, Diagnostic]:
        """Persist ``graph`` under the workspace-relative ``target`` directory.

        The output is target-specific to avoid duplicating graph artifacts:

        - ``graph/`` receives the combined ``graph.jsonl`` plus visual and query
          exports (``graph.dot`` and ``graph.cypher``).
        - ``knowledge/`` receives the node and edge JSONL files that the knowledge
          layer consumes.
        - Any other target directory receives all five files for backwards
          compatibility.
        """
        base = str(target) if target is not None else "graph"
        # Use the directory name as a stable output-profile selector. This removes
        # the previous duplication where both graph/ and knowledge/ contained the
        # same combined/visual files.
        if base == "graph":
            formats = {"jsonl", "dot", "cypher"}
        elif base == "knowledge":
            formats = {"nodes", "edges"}
        else:
            formats = {"jsonl", "nodes", "edges", "dot", "cypher"}

        try:
            self._storage.ensure_dir(base)
            if "jsonl" in formats:
                self._write_jsonl(graph, base)
            if "nodes" in formats:
                self._write_nodes_jsonl(graph, base)
            if "edges" in formats:
                self._write_edges_jsonl(graph, base)
            if "dot" in formats:
                self._write_dot(graph, base)
            if "cypher" in formats:
                self._write_cypher(graph, base)
        except Exception as exc:  # noqa: BLE001
            return Result.failure(
                Diagnostic(
                    "error",
                    "graph_storage_save_failed",
                    f"Failed to save graph to {base!r}: {exc}",
                )
            )
        return Result.success(True)

    def load(self, source: Any) -> Result[KnowledgeGraph, Diagnostic]:
        """Load a KnowledgeGraph from a persisted ``graph.jsonl`` file."""
        try:
            path = Path(str(source)) / "graph.jsonl"
            if not self._storage.exists(path):
                return Result.failure(
                    Diagnostic(
                        "error",
                        "graph_storage_load_failed",
                        f"Graph file not found: {path}",
                    )
                )
            graph = KnowledgeGraph()
            for line in self._storage.read_jsonl(str(path)):
                kind = line.get("kind")
                data = line.get("data", {})
                if kind == "GraphNode":
                    node = GraphNode.model_validate(data)
                    graph.nodes[node.id] = node
                elif kind == "GraphEdge":
                    edge = GraphEdge.model_validate(data)
                    graph.edges[edge.id] = edge
                    graph.outgoing.setdefault(edge.source_id, []).append(edge.id)
                    graph.incoming.setdefault(edge.target_id, []).append(edge.id)
                elif kind == "metadata":
                    graph.metadata.update(data)
            return Result.success(graph)
        except Exception as exc:  # noqa: BLE001
            return Result.failure(
                Diagnostic(
                    "error",
                    "graph_storage_load_failed",
                    f"Failed to load graph from {source!r}: {exc}",
                )
            )

    def _write_jsonl(self, graph: KnowledgeGraph, base: str) -> None:
        lines: list[str] = []
        if graph.metadata:
            lines.append(
                json.dumps(
                    {"kind": "metadata", "data": graph.metadata},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        for node in graph.nodes.values():
            lines.append(
                json.dumps(
                    {"kind": "GraphNode", "data": node.model_dump(mode="json")},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        for edge in graph.edges.values():
            lines.append(
                json.dumps(
                    {"kind": "GraphEdge", "data": edge.model_dump(mode="json")},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        self._storage.write_text(f"{base}/graph.jsonl", "\n".join(lines) + "\n" if lines else "")

    def _write_nodes_jsonl(self, graph: KnowledgeGraph, base: str) -> None:
        lines = [
            json.dumps(
                {"kind": "GraphNode", "data": node.model_dump(mode="json")},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            for node in graph.nodes.values()
        ]
        self._storage.write_text(
            f"{base}/graph_nodes.jsonl", "\n".join(lines) + "\n" if lines else ""
        )

    def _write_edges_jsonl(self, graph: KnowledgeGraph, base: str) -> None:
        lines = [
            json.dumps(
                {"kind": "GraphEdge", "data": edge.model_dump(mode="json")},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            for edge in graph.edges.values()
        ]
        self._storage.write_text(
            f"{base}/graph_edges.jsonl", "\n".join(lines) + "\n" if lines else ""
        )

    def _write_dot(self, graph: KnowledgeGraph, base: str) -> None:
        parts = ["digraph G {"]
        for node in graph.nodes.values():
            label = self._dot_label(node.title or node.type or node.id)
            parts.append(f'  "{self._dot_id(node.id)}" [label="{label}"];')
        for edge in graph.edges.values():
            parts.append(
                f'  "{self._dot_id(edge.source_id)}" -> "{self._dot_id(edge.target_id)}" '
                f'[label="{self._dot_label(edge.relationship_type)}"];'
            )
        parts.append("}")
        self._storage.write_text(f"{base}/graph.dot", "\n".join(parts) + "\n")

    def _write_cypher(self, graph: KnowledgeGraph, base: str) -> None:
        lines: list[str] = []
        for node in graph.nodes.values():
            title = self._cypher_string(node.title or node.type or "")
            node_type = self._cypher_string(node.type)
            lines.append(
                f'MERGE (n:Node {{id: "{self._cypher_string(node.id)}"}}) '
                f'SET n.type = "{node_type}", n.title = "{title}";'
            )
        for edge in graph.edges.values():
            rel = self._cypher_string(edge.relationship_type)
            lines.append(
                f'MATCH (a {{id: "{self._cypher_string(edge.source_id)}"}}), '
                f'(b {{id: "{self._cypher_string(edge.target_id)}"}}) '
                f'MERGE (a)-[:{rel}]->(b);'
            )
        self._storage.write_text(
            f"{base}/graph.cypher", "\n".join(lines) + "\n" if lines else ""
        )

    @staticmethod
    def _dot_id(value: str) -> str:
        return value.replace('"', '\\"').replace("\n", " ")

    @staticmethod
    def _dot_label(value: str) -> str:
        return value.replace('"', '\\"').replace("\n", " ")[:80]

    @staticmethod
    def _cypher_string(value: str) -> str:
        return value.replace('"', '\\"').replace("\n", " ")
