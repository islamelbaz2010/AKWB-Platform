"""Tests for graph traversal algorithms."""

from akwb.graph.builder import GraphBuilder
from akwb.graph.models import Direction, TraversalRequest
from akwb.graph.traversal import DefaultTraversalAlgorithm
from akwb.knowledge.models import KnowledgeCatalog


def test_bfs_order(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    traversal = DefaultTraversalAlgorithm()
    result = traversal.traverse(
        TraversalRequest(start="ku://decision-1", strategy="bfs"),
        graph,
    )
    assert result.node_ids[0] == "ku://decision-1"
    assert "ku://tech-1" in result.node_ids


def test_dfs_order(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    traversal = DefaultTraversalAlgorithm()
    result = traversal.traverse(
        TraversalRequest(start="ku://req-1", strategy="dfs"),
        graph,
    )
    assert result.node_ids[0] == "ku://req-1"


def test_shortest_path(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    traversal = DefaultTraversalAlgorithm()
    result = traversal.traverse(
        TraversalRequest(
            start="ku://req-1",
            target="ku://tech-1",
            strategy="shortest",
        ),
        graph,
    )
    assert result.path == ["ku://req-1", "ku://decision-1", "ku://tech-1"]


def test_dependency_walk(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    traversal = DefaultTraversalAlgorithm()
    result = traversal.traverse(
        TraversalRequest(
            start="ku://req-1",
            strategy="dependency",
            edge_types=["depends_on"],
        ),
        graph,
    )
    assert set(result.node_ids) == {
        "ku://req-1",
        "ku://decision-1",
        "ku://tech-1",
    }


def test_reverse_dependency_walk(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    traversal = DefaultTraversalAlgorithm()
    result = traversal.traverse(
        TraversalRequest(
            start="ku://tech-1",
            strategy="reverse_dependency",
            edge_types=["depends_on"],
        ),
        graph,
    )
    assert set(result.node_ids) == {
        "ku://tech-1",
        "ku://decision-1",
        "ku://req-1",
    }


def test_max_depth(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    traversal = DefaultTraversalAlgorithm()
    result = traversal.traverse(
        TraversalRequest(
            start="ku://req-1",
            strategy="bfs",
            max_depth=1,
            direction=Direction.OUTGOING,
        ),
        graph,
    )
    assert set(result.node_ids) == {"ku://req-1", "ku://decision-1"}
