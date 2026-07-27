"""Tests for graph statistics."""

from akwb.graph.builder import GraphBuilder
from akwb.graph.statistics import GraphStatistics
from akwb.knowledge.models import KnowledgeCatalog


def test_statistics_counts(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    stats = GraphStatistics().compute(graph)

    assert stats.node_count == 3
    assert stats.edge_count == 2
    assert stats.node_type_counts.get("decision") == 1
    assert stats.node_type_counts.get("technology") == 1
    assert stats.edge_type_counts.get("depends_on") == 2
    assert stats.connected_components == 1
    assert stats.orphan_node_count == 0


def test_cycle_count(cyclic_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(cyclic_catalog)
    stats = GraphStatistics().compute(graph)

    assert stats.cycle_count == 1
    assert stats.density > 0
