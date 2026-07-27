"""Domain models for the Enterprise Knowledge Graph Engine."""

from __future__ import annotations

from collections import deque
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from akwb.knowledge.models import (
    KnowledgeObject,
    KnowledgeRelationship,
    ReferenceKind,
)
from akwb.types import make_id


class Direction(str, Enum):
    """Direction constants for graph traversal and adjacency queries."""

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    BOTH = "both"


class GraphNode(BaseModel):
    """A node in the knowledge graph that wraps a canonical KnowledgeObject."""

    id: str
    object_id: str
    type: str
    title: str
    labels: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    incoming: list[str] = Field(default_factory=list)
    outgoing: list[str] = Field(default_factory=list)


class GraphEdge(BaseModel):
    """A typed edge between two graph nodes."""

    id: str
    relationship_type: str
    source_id: str
    target_id: str
    directed: bool = True
    properties: dict[str, Any] = Field(default_factory=dict)
    relationship_id: str | None = None


class GraphQuery(BaseModel):
    """Declarative query for graph nodes and edges."""

    node_type: str | None = None
    tags: list[str] | None = None
    domain: str | None = None
    source: str | None = None
    confidence_min: float | None = None
    confidence_max: float | None = None
    lifecycle: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] | None = None
    relationship_type: str | None = None
    edge_type: str | None = None
    limit: int | None = None


class QueryResult(BaseModel):
    """Result of a graph query."""

    node_ids: list[str] = Field(default_factory=list)
    edge_ids: list[str] = Field(default_factory=list)


class TraversalRequest(BaseModel):
    """Request for a graph traversal."""

    model_config = ConfigDict(extra="allow")

    start: str
    target: str | None = None
    strategy: str = "bfs"
    max_depth: int | None = None
    edge_types: list[str] | None = None
    direction: Direction = Direction.BOTH
    metadata: dict[str, Any] | None = None


class TraversalResult(BaseModel):
    """Result of a graph traversal."""

    node_ids: list[str] = Field(default_factory=list)
    path: list[str] = Field(default_factory=list)
    distances: dict[str, int] = Field(default_factory=dict)


class GraphStatisticsResult(BaseModel):
    """Aggregate statistics for a knowledge graph."""

    node_count: int = 0
    edge_count: int = 0
    node_type_counts: dict[str, int] = Field(default_factory=dict)
    edge_type_counts: dict[str, int] = Field(default_factory=dict)
    average_in_degree: float = 0.0
    average_out_degree: float = 0.0
    density: float = 0.0
    connected_components: int = 0
    orphan_node_count: int = 0
    cycle_count: int = 0


class KnowledgeGraph(BaseModel):
    """An in-memory, canonical graph abstraction over knowledge objects.

    Storage is abstract; persistence is handled through the ``GraphStorage``
    plugin port.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=make_id)
    metadata: dict[str, Any] = Field(default_factory=dict)
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    edges: dict[str, GraphEdge] = Field(default_factory=dict)
    outgoing: dict[str, list[str]] = Field(default_factory=dict)
    incoming: dict[str, list[str]] = Field(default_factory=dict)
    object_map: dict[str, KnowledgeObject] = Field(default_factory=dict)
    relationship_map: dict[str, KnowledgeRelationship] = Field(default_factory=dict)
    index: Any = None

    def add_node(self, obj: KnowledgeObject) -> GraphNode:
        """Add a node for ``obj`` and return it."""
        node = GraphNode(
            id=obj.id,
            object_id=obj.id,
            type=obj.type,
            title=obj.title,
            labels=[obj.type] + obj.domain_tags + obj.tags,
            properties=self._node_properties(obj),
        )
        self.nodes[obj.id] = node
        self.object_map[obj.id] = obj
        self.outgoing.setdefault(obj.id, [])
        self.incoming.setdefault(obj.id, [])
        return node

    @staticmethod
    def _node_properties(obj: KnowledgeObject) -> dict[str, Any]:
        source = obj.primary_source
        return {
            "type": obj.type,
            "domain": obj.metadata.domain,
            "project_id": obj.metadata.project_id,
            "lifecycle": obj.lifecycle.state.value,
            "confidence": obj.confidence.value,
            "source": source.kind if source else None,
            "tags": obj.tags + obj.domain_tags,
            "title": obj.title,
            "description": obj.description,
        }

    def add_edge(
        self,
        rel: KnowledgeRelationship,
        directed: bool = True,
        reference: bool = False,
    ) -> GraphEdge | None:
        """Add an edge for a relationship, respecting object references only."""
        if rel.from_ref.kind != ReferenceKind.KNOWLEDGE_OBJECT:
            return None
        if rel.to_ref.kind != ReferenceKind.KNOWLEDGE_OBJECT:
            return None

        source_id = rel.from_ref.ref
        target_id = rel.to_ref.ref

        edge = GraphEdge(
            id=rel.id,
            relationship_type=rel.relationship_type,
            source_id=source_id,
            target_id=target_id,
            directed=directed,
            properties={
                "confidence": rel.confidence.value,
                "project_id": rel.metadata.project_id,
                "domain": rel.metadata.domain,
                "evidence_count": len(rel.evidence),
            },
            relationship_id=rel.id,
        )
        self.edges[rel.id] = edge
        self.relationship_map[rel.id] = rel
        self._wire_adjacency(edge, directed)
        return edge

    def add_reference_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str = "references",
        directed: bool = True,
    ) -> GraphEdge | None:
        """Add a synthetic edge from an object's ``references`` list."""
        edge_id = f"ref:{source_id}->{target_id}"
        if edge_id in self.edges:
            return self.edges[edge_id]

        edge = GraphEdge(
            id=edge_id,
            relationship_type=relationship_type,
            source_id=source_id,
            target_id=target_id,
            directed=directed,
            properties={"synthetic": True},
        )
        self.edges[edge_id] = edge
        self._wire_adjacency(edge, directed)
        return edge

    def _wire_adjacency(self, edge: GraphEdge, directed: bool) -> None:
        source_id = edge.source_id
        target_id = edge.target_id

        self.outgoing.setdefault(source_id, []).append(edge.id)
        self.incoming.setdefault(target_id, []).append(edge.id)

        if not directed:
            self.outgoing.setdefault(target_id, []).append(edge.id)
            self.incoming.setdefault(source_id, []).append(edge.id)

    def get_node(self, node_id: str) -> GraphNode | None:
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        return self.edges.get(edge_id)

    def get_object(self, node_id: str) -> KnowledgeObject | None:
        return self.object_map.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        return [self.edges[eid] for eid in self.outgoing.get(node_id, []) if eid in self.edges]

    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        return [self.edges[eid] for eid in self.incoming.get(node_id, []) if eid in self.edges]

    def _other_endpoint(self, edge: GraphEdge, node_id: str) -> str:
        return edge.target_id if edge.source_id == node_id else edge.source_id

    def neighbors(
        self,
        node_id: str,
        direction: Direction = Direction.BOTH,
        edge_types: list[str] | None = None,
    ) -> set[str]:
        """Return neighbor node ids reachable from ``node_id``."""
        results: set[str] = set()

        def visit(edges: list[GraphEdge]) -> None:
            for edge in edges:
                if edge_types and edge.relationship_type not in edge_types:
                    continue
                other = self._other_endpoint(edge, node_id)
                results.add(other)

        if direction in {Direction.OUTGOING, Direction.BOTH}:
            visit(self.get_outgoing_edges(node_id))
        if direction in {Direction.INCOMING, Direction.BOTH}:
            visit(self.get_incoming_edges(node_id))

        return results

    def descendants(self, node_id: str, max_depth: int | None = None) -> set[str]:
        """Return all nodes reachable by following outgoing directed edges."""
        return self._reachable(node_id, Direction.OUTGOING, max_depth)

    def ancestors(self, node_id: str, max_depth: int | None = None) -> set[str]:
        """Return all nodes reachable by following incoming directed edges."""
        return self._reachable(node_id, Direction.INCOMING, max_depth)

    def _reachable(
        self,
        node_id: str,
        direction: Direction,
        max_depth: int | None,
    ) -> set[str]:
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(node_id, 0)])
        while queue:
            current, depth = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            if max_depth is not None and depth >= max_depth:
                continue
            edges = (
                self.get_outgoing_edges(current)
                if direction == Direction.OUTGOING
                else self.get_incoming_edges(current)
            )
            for edge in edges:
                if edge.directed:
                    next_id = (
                        edge.target_id
                        if direction == Direction.OUTGOING
                        else edge.source_id
                    )
                else:
                    next_id = self._other_endpoint(edge, current)
                if next_id not in visited:
                    queue.append((next_id, depth + 1))
        visited.discard(node_id)
        return visited

    def neighborhood(self, node_id: str, radius: int = 1) -> set[str]:
        """Return nodes within ``radius`` hops using both directions."""
        return self._reachable(node_id, Direction.BOTH, radius)

    def connected_components(self) -> list[set[str]]:
        """Return connected components treating edges as undirected."""
        visited: set[str] = set()
        components: list[set[str]] = []

        for node_id in self.nodes:
            if node_id in visited:
                continue
            component: set[str] = set()
            queue: deque[str] = deque([node_id])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                for neighbor in self.neighbors(current, direction=Direction.BOTH):
                    if neighbor not in visited:
                        queue.append(neighbor)
            components.append(component)

        return components

    def has_path(self, source: str, target: str) -> bool:
        """Return True if ``target`` is reachable from ``source``."""
        return target in self.descendants(source) or source == target

    def shortest_path(self, source: str, target: str) -> list[str]:
        """Return the shortest node-id path from ``source`` to ``target`` using BFS."""
        if source == target:
            return [source]

        queue: deque[tuple[str, list[str]]] = deque([(source, [source])])
        visited: set[str] = {source}

        while queue:
            current, path = queue.popleft()
            for edge in self.get_outgoing_edges(current):
                if not edge.directed:
                    continue
                next_id = edge.target_id
                if next_id in visited:
                    continue
                new_path = path + [next_id]
                if next_id == target:
                    return new_path
                visited.add(next_id)
                queue.append((next_id, new_path))

        return []

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)
