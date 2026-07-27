"""Tests for the graph index and query engine."""

from akwb.graph.index import DefaultGraphQueryEngine, InMemoryGraphIndex
from akwb.graph.models import GraphQuery, KnowledgeGraph
from akwb.knowledge.models import KnowledgeCatalog


def _build_graph(catalog: KnowledgeCatalog) -> KnowledgeGraph:
    from akwb.graph.builder import GraphBuilder

    return GraphBuilder().build(catalog)


def test_index_by_type(sample_catalog: KnowledgeCatalog) -> None:
    graph = _build_graph(sample_catalog)
    index = InMemoryGraphIndex().build(graph)

    result = index.search(GraphQuery(node_type="decision"))
    assert result == {"ku://decision-1"}


def test_index_by_tag(sample_catalog: KnowledgeCatalog) -> None:
    graph = _build_graph(sample_catalog)
    index = InMemoryGraphIndex().build(graph)

    result = index.search(GraphQuery(tags=["database"]))
    assert "ku://decision-1" in result
    assert "ku://tech-1" in result
    assert "ku://req-1" not in result


def test_query_engine_returns_nodes_and_edges(sample_catalog: KnowledgeCatalog) -> None:
    graph = _build_graph(sample_catalog)
    engine = DefaultGraphQueryEngine()

    result = engine.execute(GraphQuery(relationship_type="depends_on"), graph)
    assert "ku://decision-1" in result.node_ids
    assert "ku://tech-1" in result.node_ids
    assert len(result.edge_ids) == 2


def test_query_by_confidence_range(sample_catalog: KnowledgeCatalog) -> None:
    graph = _build_graph(sample_catalog)
    engine = DefaultGraphQueryEngine()

    result = engine.execute(GraphQuery(confidence_min=0.5, confidence_max=1.0), graph)
    assert "ku://decision-1" in result.node_ids


def test_query_by_project_id(sample_catalog: KnowledgeCatalog) -> None:
    graph = _build_graph(sample_catalog)
    engine = DefaultGraphQueryEngine()

    result = engine.execute(GraphQuery(project_id="akwb"), graph)
    assert len(result.node_ids) == 3


def test_query_edge_type(sample_catalog: KnowledgeCatalog) -> None:
    graph = _build_graph(sample_catalog)
    engine = DefaultGraphQueryEngine()

    result = engine.execute(GraphQuery(edge_type="depends_on"), graph)
    assert len(result.edge_ids) == 2
    assert result.node_ids == []
