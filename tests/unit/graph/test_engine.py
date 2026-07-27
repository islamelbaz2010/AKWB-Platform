"""Tests for the graph engine orchestrator."""

from akwb.graph.engine import GraphEngine
from akwb.graph.models import GraphQuery, TraversalRequest
from akwb.knowledge.models import KnowledgeCatalog


def test_engine_builds_and_queries(sample_catalog: KnowledgeCatalog) -> None:
    engine = GraphEngine()
    graph = engine.build(sample_catalog)

    assert graph.node_count() == 3
    assert graph.index is not None

    result = engine.query(graph, GraphQuery(node_type="decision"))
    assert result.node_ids == ["ku://decision-1"]


def test_engine_traversal(sample_catalog: KnowledgeCatalog) -> None:
    engine = GraphEngine()
    graph = engine.build(sample_catalog)

    result = engine.traverse(
        graph,
        TraversalRequest(start="ku://req-1", strategy="dependency"),
    )
    assert "ku://tech-1" in result.node_ids


def test_engine_validation_and_statistics(sample_catalog: KnowledgeCatalog) -> None:
    engine = GraphEngine()
    graph = engine.build(sample_catalog)

    validation = engine.validate(graph)
    assert validation.ok

    stats = engine.statistics(graph)
    assert stats.node_count == 3


def test_engine_load_without_storage_raises() -> None:
    engine = GraphEngine()
    import pytest

    with pytest.raises(RuntimeError):
        engine.load("any")
