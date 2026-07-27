"""Graph validation for the Enterprise Knowledge Graph Engine."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from akwb.graph.models import GraphEdge, KnowledgeGraph
from akwb.knowledge.validation import ValidationResult
from akwb.types import Diagnostic


class GraphValidator:
    """Validate a KnowledgeGraph and produce diagnostics."""

    def __init__(self, framework: Any | None = None) -> None:
        self.framework = framework

    def validate(self, graph: KnowledgeGraph) -> ValidationResult:
        """Run all graph validations and return a merged result."""
        result = ValidationResult.success()
        result.merge(self._broken_references(graph))
        result.merge(self._cycles(graph))
        result.merge(self._duplicate_edges(graph))
        result.merge(self._orphan_nodes(graph))
        result.merge(self._invalid_relationships(graph))
        return result

    def _broken_references(self, graph: KnowledgeGraph) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        for edge in graph.edges.values():
            if edge.source_id not in graph.nodes:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "broken_reference",
                        f"Edge {edge.id!r} references missing source node {edge.source_id!r}",
                        source_ref=edge.id,
                    )
                )
            if edge.target_id not in graph.nodes:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "broken_reference",
                        f"Edge {edge.id!r} references missing target node {edge.target_id!r}",
                        source_ref=edge.id,
                    )
                )
        return ValidationResult(ok=not diagnostics, diagnostics=diagnostics)

    def _cycles(self, graph: KnowledgeGraph) -> ValidationResult:
        diagnostics: list[Diagnostic] = []

        directed: dict[str, list[str]] = defaultdict(list)
        for edge in graph.edges.values():
            if (
                edge.directed
                and edge.source_id in graph.nodes
                and edge.target_id in graph.nodes
            ):
                directed[edge.source_id].append(edge.target_id)

        # Color states: 0 = unvisited, 1 = visiting, 2 = done
        state: dict[str, int] = {n: 0 for n in graph.nodes}
        path: list[str] = []

        for start in list(state.keys()):
            if state[start] != 0:
                continue

            stack: list[tuple[str, int]] = [(start, 0)]
            state[start] = 1
            path.append(start)

            while stack:
                node, idx = stack[-1]
                neighbors = directed.get(node, [])

                if idx < len(neighbors):
                    stack[-1] = (node, idx + 1)
                    nxt = neighbors[idx]

                    if state.get(nxt, 0) == 1:
                        cycle_start = path.index(nxt)
                        cycle = path[cycle_start:] + [nxt]
                        diagnostics.append(
                            Diagnostic(
                                "error",
                                "cycle",
                                f"Directed cycle detected: {' -> '.join(cycle)}",
                            )
                        )
                        continue

                    if state.get(nxt, 0) == 0:
                        state[nxt] = 1
                        path.append(nxt)
                        stack.append((nxt, 0))
                else:
                    state[node] = 2
                    stack.pop()
                    path.pop()

        return ValidationResult(ok=not diagnostics, diagnostics=diagnostics)

    def _duplicate_edges(self, graph: KnowledgeGraph) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        seen: dict[tuple[str, str, str], list[str]] = defaultdict(list)

        for edge in graph.edges.values():
            key = self._edge_key(edge)
            seen[key].append(edge.id)

        for key, edge_ids in seen.items():
            if len(edge_ids) > 1:
                source, target, rel_type = key
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "duplicate_edge",
                        f"Duplicate {rel_type!r} edges between {source!r} and {target!r}: {edge_ids}",
                    )
                )

        return ValidationResult(ok=not diagnostics, diagnostics=diagnostics)

    @staticmethod
    def _edge_key(edge: GraphEdge) -> tuple[str, str, str]:
        if edge.directed:
            return (edge.source_id, edge.target_id, edge.relationship_type)
        return (
            min(edge.source_id, edge.target_id),
            max(edge.source_id, edge.target_id),
            edge.relationship_type,
        )

    def _orphan_nodes(self, graph: KnowledgeGraph) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        for node_id in graph.nodes:
            has_edges = bool(
                graph.outgoing.get(node_id) or graph.incoming.get(node_id)
            )
            if not has_edges:
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "orphan_node",
                        f"Node {node_id!r} has no edges",
                    )
                )
        return ValidationResult(ok=not diagnostics, diagnostics=diagnostics)

    def _invalid_relationships(self, graph: KnowledgeGraph) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        if self.framework is None:
            return ValidationResult.success()

        for edge in graph.edges.values():
            rel_type = self.framework.get_relationship_type(edge.relationship_type)
            if rel_type is None:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invalid_relationship_type",
                        f"Relationship type {edge.relationship_type!r} is not registered",
                        source_ref=edge.id,
                    )
                )
                continue

            source_obj = graph.get_object(edge.source_id)
            target_obj = graph.get_object(edge.target_id)
            if (
                rel_type.allowed_from_types
                and source_obj
                and source_obj.type not in rel_type.allowed_from_types
            ):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invalid_relationship_source",
                        f"Node {edge.source_id!r} type {source_obj.type!r} not allowed as source for {edge.relationship_type!r}",
                        source_ref=edge.id,
                    )
                )
            if (
                rel_type.allowed_to_types
                and target_obj
                and target_obj.type not in rel_type.allowed_to_types
            ):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invalid_relationship_target",
                        f"Node {edge.target_id!r} type {target_obj.type!r} not allowed as target for {edge.relationship_type!r}",
                        source_ref=edge.id,
                    )
                )

        return ValidationResult(ok=not diagnostics, diagnostics=diagnostics)
