"""Enterprise Knowledge Graph Engine orchestrator."""

from __future__ import annotations

from typing import Any

from akwb.graph.builder import GraphBuilder
from akwb.graph.index import InMemoryGraphIndex
from akwb.graph.models import (
    GraphQuery,
    GraphStatisticsResult,
    KnowledgeGraph,
    QueryResult,
    TraversalRequest,
    TraversalResult,
)
from akwb.graph.plugins import (
    GraphIndexer,
    GraphQueryEngine,
    GraphStorage,
    TraversalAlgorithm,
)
from akwb.graph.statistics import GraphStatistics
from akwb.graph.traversal import DefaultTraversalAlgorithm
from akwb.graph.validation import GraphValidator
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.validation import ValidationResult

if __name__ == "__main__":
    pass


class GraphEngine:
    """Orchestrate graph building, indexing, querying, traversal, validation, and statistics.

    All backends (storage, query, traversal, index) are replaceable through the
    plugin system.
    """

    def __init__(
        self,
        framework: KnowledgeFramework | None = None,
        plugin_registry: Any | None = None,
    ) -> None:
        self.framework = framework or KnowledgeFramework()
        self.storage: GraphStorage | None = None
        self.query_engine: GraphQueryEngine = self._default_query_engine()
        self.traversal: TraversalAlgorithm = DefaultTraversalAlgorithm()
        self.indexer: GraphIndexer = InMemoryGraphIndex()

        if plugin_registry:
            self.load_plugins(plugin_registry)

    def load_plugins(self, plugin_registry: Any) -> None:
        """Replace built-in components with plugin-provided implementations."""
        for storage in plugin_registry.resolve("graph_storage"):
            self.storage = self._instantiate(storage)

        for query_engine in plugin_registry.resolve("graph_query_engine"):
            self.query_engine = self._instantiate(query_engine)

        for traversal in plugin_registry.resolve("graph_traversal"):
            self.traversal = self._instantiate(traversal)

        for indexer in plugin_registry.resolve("graph_index"):
            self.indexer = self._instantiate(indexer)

    @staticmethod
    def _instantiate(component: Any) -> Any:
        return component() if isinstance(component, type) else component

    @staticmethod
    def _default_query_engine() -> GraphQueryEngine:
        from akwb.graph.index import DefaultGraphQueryEngine

        return DefaultGraphQueryEngine()

    def build(self, catalog: Any) -> KnowledgeGraph:
        """Build and index a KnowledgeGraph from a KnowledgeCatalog."""
        builder = GraphBuilder(self.framework)
        graph = builder.build(catalog)
        graph.index = self.indexer.build(graph)
        return graph

    def query(self, graph: KnowledgeGraph, query: GraphQuery) -> QueryResult:
        """Execute a query against the graph."""
        if graph.index is None:
            graph.index = self.indexer.build(graph)
        return self.query_engine.execute(query, graph)

    def traverse(
        self,
        graph: KnowledgeGraph,
        request: TraversalRequest,
    ) -> TraversalResult:
        """Run a traversal over the graph."""
        return self.traversal.traverse(request, graph)

    def validate(self, graph: KnowledgeGraph) -> ValidationResult:
        """Validate the graph structure and relationships."""
        return GraphValidator(self.framework).validate(graph)

    def statistics(self, graph: KnowledgeGraph) -> GraphStatisticsResult:
        """Return aggregate graph statistics."""
        return GraphStatistics().compute(graph)

    def save(self, graph: KnowledgeGraph, target: Any) -> Any:
        """Persist a graph using the configured storage backend."""
        if self.storage is None:
            raise RuntimeError("No graph storage backend configured")
        return self.storage.save(graph, target)

    def load(self, source: Any) -> Any:
        """Load a graph using the configured storage backend."""
        if self.storage is None:
            raise RuntimeError("No graph storage backend configured")
        return self.storage.load(source)
