"""Graph indexing implementation and plugin port."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from akwb.graph.models import GraphEdge, GraphNode, GraphQuery, KnowledgeGraph, QueryResult
from akwb.graph.plugins import GraphIndexer, GraphQueryEngine


class InMemoryGraphIndex(GraphIndexer):
    """In-memory inverted indexes for fast graph queries."""

    def __init__(self) -> None:
        self.all_nodes: set[str] = set()
        self.by_type: dict[str, set[str]] = defaultdict(set)
        self.by_tag: dict[str, set[str]] = defaultdict(set)
        self.by_domain: dict[str, set[str]] = defaultdict(set)
        self.by_source: dict[str, set[str]] = defaultdict(set)
        self.by_lifecycle: dict[str, set[str]] = defaultdict(set)
        self.by_project: dict[str, set[str]] = defaultdict(set)
        self.by_metadata: dict[str, dict[Any, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.confidence: list[tuple[float, str]] = []
        self.by_relationship_type: dict[str, set[str]] = defaultdict(set)
        self.edge_by_type: dict[str, set[str]] = defaultdict(set)

    def build(self, graph: KnowledgeGraph) -> InMemoryGraphIndex:
        """Populate indexes from ``graph``."""
        self.all_nodes = set(graph.nodes.keys())
        for node_id, node in graph.nodes.items():
            self._index_node(node_id, node, graph)
        for edge_id, edge in graph.edges.items():
            self._index_edge(edge_id, edge)
        return self

    def _index_node(
        self,
        node_id: str,
        node: GraphNode,
        graph: KnowledgeGraph,
    ) -> None:
        self.by_type[node.type].add(node_id)

        for label in node.labels:
            self.by_tag[label].add(node_id)

        for tag in node.properties.get("tags", []):
            self.by_tag[tag].add(node_id)

        domain = node.properties.get("domain")
        if domain:
            self.by_domain[domain].add(node_id)

        source = node.properties.get("source")
        if source:
            self.by_source[source].add(node_id)

        lifecycle = node.properties.get("lifecycle")
        if lifecycle:
            self.by_lifecycle[lifecycle].add(node_id)

        project_id = node.properties.get("project_id")
        if project_id:
            self.by_project[project_id].add(node_id)

        confidence = node.properties.get("confidence")
        if confidence is not None:
            self.confidence.append((float(confidence), node_id))

        obj = graph.get_object(node_id)
        if obj:
            for key, value in obj.metadata.custom.items():
                self.by_metadata[key][value].add(node_id)

    def _index_edge(self, edge_id: str, edge: GraphEdge) -> None:
        self.by_relationship_type[edge.relationship_type].add(edge.source_id)
        self.by_relationship_type[edge.relationship_type].add(edge.target_id)
        self.edge_by_type[edge.relationship_type].add(edge_id)

    def search(self, query: GraphQuery) -> set[str]:
        """Return node ids matching the query."""
        candidates: set[str] | None = None

        if query.node_type:
            candidates = self._intersect(candidates, self.by_type.get(query.node_type, set()))

        if query.tags:
            for tag in query.tags:
                candidates = self._intersect(candidates, self.by_tag.get(tag, set()))

        if query.domain:
            candidates = self._intersect(candidates, self.by_domain.get(query.domain, set()))

        if query.source:
            candidates = self._intersect(candidates, self.by_source.get(query.source, set()))

        if query.lifecycle:
            candidates = self._intersect(
                candidates,
                self.by_lifecycle.get(query.lifecycle, set()),
            )

        if query.project_id:
            candidates = self._intersect(
                candidates,
                self.by_project.get(query.project_id, set()),
            )

        if query.relationship_type:
            candidates = self._intersect(
                candidates,
                self.by_relationship_type.get(query.relationship_type, set()),
            )

        if query.metadata:
            for key, value in query.metadata.items():
                value_map = self.by_metadata.get(key, {})
                candidates = self._intersect(candidates, value_map.get(value, set()))

        node_ids: set[str] = (
            candidates if candidates is not None else set(self.all_nodes)
        )

        if query.confidence_min is not None or query.confidence_max is not None:
            node_ids = self._filter_confidence(
                node_ids,
                query.confidence_min,
                query.confidence_max,
            )

        if query.limit:
            node_ids = set(sorted(node_ids)[: query.limit])

        return node_ids

    def search_edges(self, query: GraphQuery) -> set[str]:
        """Return edge ids matching the query's ``edge_type``."""
        if query.edge_type:
            return set(self.edge_by_type.get(query.edge_type, set()))
        if query.relationship_type:
            return set(self.edge_by_type.get(query.relationship_type, set()))
        return set()

    @staticmethod
    def _intersect(
        current: set[str] | None,
        other: set[str],
    ) -> set[str]:
        if current is None:
            return set(other)
        return current & other

    def _filter_confidence(
        self,
        node_ids: set[str],
        min_value: float | None,
        max_value: float | None,
    ) -> set[str]:
        allowed: set[str] = set()
        for value, nid in self.confidence:
            if nid not in node_ids:
                continue
            if min_value is not None and value < min_value:
                continue
            if max_value is not None and value > max_value:
                continue
            allowed.add(nid)
        return allowed


class DefaultGraphQueryEngine(GraphQueryEngine):
    """Built-in query engine backed by an in-memory graph index."""

    def execute(self, query: GraphQuery, graph: KnowledgeGraph) -> QueryResult:
        """Return node and edge ids matching ``query``."""
        index = graph.index
        if index is None or not isinstance(index, InMemoryGraphIndex):
            index = InMemoryGraphIndex().build(graph)
            graph.index = index

        node_ids = self._search_nodes(index, query)
        edge_ids = index.search_edges(query)

        # Filter node results by their actual properties when the index cannot.
        if query.confidence_min is not None or query.confidence_max is not None:
            node_ids = self._filter_node_confidence(
                graph,
                node_ids,
                query.confidence_min,
                query.confidence_max,
            )

        if query.limit:
            node_ids = set(sorted(node_ids)[: query.limit])

        return QueryResult(
            node_ids=sorted(node_ids),
            edge_ids=sorted(edge_ids),
        )

    @staticmethod
    def _search_nodes(index: InMemoryGraphIndex, query: GraphQuery) -> set[str]:
        """Return node ids when node-level criteria are present."""
        has_node_criteria = any(
            [
                query.node_type,
                query.tags,
                query.domain,
                query.source,
                query.lifecycle,
                query.project_id,
                query.metadata,
                query.relationship_type,
                query.confidence_min is not None,
                query.confidence_max is not None,
            ]
        )

        if query.edge_type and not has_node_criteria:
            return set()

        if has_node_criteria:
            return index.search(query)

        return set(index.all_nodes)

    @staticmethod
    def _filter_node_confidence(
        graph: KnowledgeGraph,
        node_ids: set[str],
        min_value: float | None,
        max_value: float | None,
    ) -> set[str]:
        filtered: set[str] = set()
        for node_id in node_ids:
            node = graph.get_node(node_id)
            if node is None:
                continue
            value = node.properties.get("confidence")
            if not isinstance(value, (int, float)):
                continue
            if min_value is not None and value < min_value:
                continue
            if max_value is not None and value > max_value:
                continue
            filtered.add(node_id)
        return filtered
