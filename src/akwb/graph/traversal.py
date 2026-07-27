"""Graph traversal algorithms and plugin port implementation."""

from __future__ import annotations

from collections import deque

from akwb.graph.models import (
    Direction,
    GraphEdge,
    KnowledgeGraph,
    TraversalRequest,
    TraversalResult,
)
from akwb.graph.plugins import TraversalAlgorithm


class DefaultTraversalAlgorithm(TraversalAlgorithm):
    """Built-in traversal algorithms: BFS, DFS, shortest path, dependency walks."""

    def traverse(
        self,
        request: TraversalRequest,
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        strategy = request.strategy.lower()
        if strategy == "bfs":
            return self._bfs(graph, request)
        if strategy == "dfs":
            return self._dfs(graph, request)
        if strategy == "shortest":
            return self._shortest_path(graph, request)
        if strategy == "dependency":
            return self._dependency_walk(graph, request)
        if strategy == "reverse_dependency":
            return self._reverse_dependency_walk(graph, request)
        raise ValueError(f"Unknown traversal strategy: {request.strategy!r}")

    def _bfs(
        self,
        graph: KnowledgeGraph,
        request: TraversalRequest,
    ) -> TraversalResult:
        visited: set[str] = set()
        order: list[str] = []
        distances: dict[str, int] = {}
        queue: deque[tuple[str, int]] = deque([(request.start, 0)])

        while queue:
            current, depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            order.append(current)
            distances[current] = depth

            if request.max_depth is not None and depth >= request.max_depth:
                continue

            for edge in self._select_edges(graph, current, request):
                next_id = self._next_node(edge, current)
                if next_id and next_id not in visited:
                    queue.append((next_id, depth + 1))

        return TraversalResult(node_ids=order, distances=distances)

    def _dfs(
        self,
        graph: KnowledgeGraph,
        request: TraversalRequest,
    ) -> TraversalResult:
        visited: set[str] = set()
        order: list[str] = []
        distances: dict[str, int] = {}

        def visit(node_id: str, depth: int) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            order.append(node_id)
            distances[node_id] = depth

            if request.max_depth is not None and depth >= request.max_depth:
                return

            for edge in self._select_edges(graph, node_id, request):
                next_id = self._next_node(edge, node_id)
                if next_id and next_id not in visited:
                    visit(next_id, depth + 1)

        visit(request.start, 0)
        return TraversalResult(node_ids=order, distances=distances)

    def _shortest_path(
        self,
        graph: KnowledgeGraph,
        request: TraversalRequest,
    ) -> TraversalResult:
        if request.target is None:
            raise ValueError("Shortest path traversal requires a 'target' parameter")
        target = request.target

        if request.start == target:
            return TraversalResult(node_ids=[request.start], path=[request.start])

        visited: set[str] = {request.start}
        queue: deque[tuple[str, list[str]]] = deque([(request.start, [request.start])])

        while queue:
            current, path = queue.popleft()
            for edge in self._select_edges(
                graph,
                current,
                request,
                outgoing_only=True,
            ):
                if not edge.directed:
                    continue
                next_id = edge.target_id
                if next_id in visited:
                    continue
                new_path = path + [next_id]
                if next_id == target:
                    return TraversalResult(node_ids=new_path, path=new_path)
                visited.add(next_id)
                queue.append((next_id, new_path))

        return TraversalResult(node_ids=[])

    def _dependency_walk(
        self,
        graph: KnowledgeGraph,
        request: TraversalRequest,
    ) -> TraversalResult:
        request.direction = Direction.OUTGOING
        return self._bfs(graph, request)

    def _reverse_dependency_walk(
        self,
        graph: KnowledgeGraph,
        request: TraversalRequest,
    ) -> TraversalResult:
        request.direction = Direction.INCOMING
        return self._bfs(graph, request)

    def _select_edges(
        self,
        graph: KnowledgeGraph,
        node_id: str,
        request: TraversalRequest,
        outgoing_only: bool = False,
    ) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        if outgoing_only or request.direction in {Direction.OUTGOING, Direction.BOTH}:
            edges.extend(graph.get_outgoing_edges(node_id))
        if not outgoing_only and request.direction in {Direction.INCOMING, Direction.BOTH}:
            edges.extend(graph.get_incoming_edges(node_id))

        if request.edge_types:
            edges = [e for e in edges if e.relationship_type in request.edge_types]

        return edges

    @staticmethod
    def _next_node(edge: GraphEdge, current: str) -> str | None:
        if edge.source_id == current:
            return edge.target_id
        if edge.target_id == current:
            return edge.source_id
        return None
