"""Graph statistics for the Enterprise Knowledge Graph Engine."""

from __future__ import annotations

from collections import Counter

from akwb.graph.models import GraphStatisticsResult, KnowledgeGraph


class GraphStatistics:
    """Compute aggregate statistics for a knowledge graph."""

    def compute(self, graph: KnowledgeGraph) -> GraphStatisticsResult:
        """Return a full statistics snapshot."""
        node_count = graph.node_count()
        edge_count = graph.edge_count()

        node_type_counts = Counter(node.type for node in graph.nodes.values())
        edge_type_counts = Counter(edge.relationship_type for edge in graph.edges.values())

        total_out_degree = sum(len(edges) for edges in graph.outgoing.values())
        total_in_degree = sum(len(edges) for edges in graph.incoming.values())

        avg_out = total_out_degree / node_count if node_count else 0.0
        avg_in = total_in_degree / node_count if node_count else 0.0

        density = self._density(node_count, edge_count)
        components = len(graph.connected_components())
        orphan_count = self._orphan_count(graph)
        cycle_count = self._cycle_count(graph)

        return GraphStatisticsResult(
            node_count=node_count,
            edge_count=edge_count,
            node_type_counts=dict(node_type_counts),
            edge_type_counts=dict(edge_type_counts),
            average_in_degree=avg_in,
            average_out_degree=avg_out,
            density=density,
            connected_components=components,
            orphan_node_count=orphan_count,
            cycle_count=cycle_count,
        )

    @staticmethod
    def _density(node_count: int, edge_count: int) -> float:
        if node_count < 2:
            return 0.0
        # Directed simple graph density.
        return edge_count / (node_count * (node_count - 1))

    @staticmethod
    def _orphan_count(graph: KnowledgeGraph) -> int:
        return sum(
            1
            for node_id in graph.nodes
            if not graph.outgoing.get(node_id) and not graph.incoming.get(node_id)
        )

    def _cycle_count(self, graph: KnowledgeGraph) -> int:
        sccs = self._tarjan(graph)
        count = 0
        for component in sccs:
            if len(component) > 1:
                count += 1
            elif len(component) == 1:
                node = component[0]
                if any(
                    edge.source_id == node and edge.target_id == node and edge.directed
                    for edge in graph.edges.values()
                ):
                    count += 1
        return count

    def _tarjan(self, graph: KnowledgeGraph) -> list[list[str]]:
        """Return strongly connected components using Tarjan's algorithm."""
        directed: dict[str, list[str]] = {}
        for node_id in graph.nodes:
            directed[node_id] = []
        for edge in graph.edges.values():
            if edge.directed and edge.source_id in graph.nodes and edge.target_id in graph.nodes:
                directed[edge.source_id].append(edge.target_id)

        index_counter = 0
        stack: list[str] = []
        on_stack: set[str] = set()
        index: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        sccs: list[list[str]] = []

        def strongconnect(node: str) -> None:
            nonlocal index_counter
            index[node] = index_counter
            lowlink[node] = index_counter
            index_counter += 1
            stack.append(node)
            on_stack.add(node)

            for successor in directed.get(node, []):
                if successor not in index:
                    strongconnect(successor)
                    lowlink[node] = min(lowlink[node], lowlink[successor])
                elif successor in on_stack:
                    lowlink[node] = min(lowlink[node], index[successor])

            if lowlink[node] == index[node]:
                component: list[str] = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    component.append(w)
                    if w == node:
                        break
                sccs.append(component)

        for node in list(directed.keys()):
            if node not in index:
                strongconnect(node)

        return sccs
