"""Plugin extension ports for the Enterprise Knowledge Graph Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from akwb.domain.ports import PluginPort
from akwb.types import Diagnostic, Result

if TYPE_CHECKING:
    from akwb.graph.models import (
        GraphQuery,
        KnowledgeGraph,
        QueryResult,
        TraversalRequest,
        TraversalResult,
    )


class GraphStorage(PluginPort, ABC):
    """Abstract storage backend for persisting and loading knowledge graphs."""

    port_name = "graph_storage"

    @abstractmethod
    def save(self, graph: KnowledgeGraph, target: Any) -> Result[bool, Diagnostic]:
        """Persist ``graph`` to ``target``."""
        ...

    @abstractmethod
    def load(self, source: Any) -> Result[KnowledgeGraph, Diagnostic]:
        """Load a graph from ``source``."""
        ...


class GraphQueryEngine(PluginPort, ABC):
    """Abstract query engine for searching the knowledge graph."""

    port_name = "graph_query_engine"

    @abstractmethod
    def execute(self, query: GraphQuery, graph: KnowledgeGraph) -> QueryResult:
        """Execute ``query`` against ``graph`` and return matching node/edge ids."""
        ...


class TraversalAlgorithm(PluginPort, ABC):
    """Abstract traversal algorithm for graph walks."""

    port_name = "graph_traversal"

    @abstractmethod
    def traverse(
        self,
        request: TraversalRequest,
        graph: KnowledgeGraph,
    ) -> TraversalResult:
        """Run a traversal and return the result."""
        ...


class GraphIndexer(PluginPort, ABC):
    """Abstract graph index builder and searcher."""

    port_name = "graph_index"

    @abstractmethod
    def build(self, graph: KnowledgeGraph) -> GraphIndexer:
        """Index ``graph`` and return the indexer instance."""
        ...

    @abstractmethod
    def search(self, query: GraphQuery) -> set[str]:
        """Return node ids matching ``query``."""
        ...
