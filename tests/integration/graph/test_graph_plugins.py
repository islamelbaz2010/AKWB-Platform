"""Integration tests for graph engine plugin ports."""

from pathlib import Path

import pytest

from akwb.graph.engine import GraphEngine
from akwb.graph.models import GraphQuery
from akwb.knowledge.models import KnowledgeCatalog
from akwb.plugins.registry import PluginRegistry


@pytest.fixture
def graph_plugin_dir() -> Path:
    return Path(__file__).parent.parent.parent / "fixtures" / "graph_plugin"


def test_plugin_query_engine_override(
    graph_plugin_dir: Path,
    sample_catalog: KnowledgeCatalog,
) -> None:
    registry = PluginRegistry()
    result = registry.load_from_directory(graph_plugin_dir)
    assert result.ok, result.error

    engine = GraphEngine(plugin_registry=registry)
    graph = engine.build(sample_catalog)
    query_result = engine.query(graph, GraphQuery(limit=2))

    expected = sorted(graph.nodes.keys(), reverse=True)[:2]
    assert query_result.node_ids == expected
