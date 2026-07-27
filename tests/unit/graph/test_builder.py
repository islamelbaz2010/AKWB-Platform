"""Tests for the graph builder."""

from akwb.graph.builder import GraphBuilder
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    ReferenceKind,
)


def test_build_from_catalog(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)

    assert graph.node_count() == 3
    assert graph.edge_count() == 2
    assert "ku://decision-1" in graph.nodes
    assert graph.get_outgoing_edges("ku://decision-1")[0].target_id == "ku://tech-1"


def test_build_uses_relationship_direction(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder(framework=KnowledgeFramework()).build(sample_catalog)
    edge = graph.get_edge("rel-1")
    assert edge is not None
    assert edge.directed is True


def test_build_with_undirected_related_to() -> None:
    framework = KnowledgeFramework()
    catalog = framework.new_catalog()

    a = KnowledgeObject(id="ku://a", type="component", title="A")
    b = KnowledgeObject(id="ku://b", type="component", title="B")
    catalog.add_object(a)
    catalog.add_object(b)
    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-related",
            relationship_type="related_to",
            from_ref=KnowledgeReference(
                kind=ReferenceKind.KNOWLEDGE_OBJECT, ref=a.id
            ),
            to_ref=KnowledgeReference(
                kind=ReferenceKind.KNOWLEDGE_OBJECT, ref=b.id
            ),
        )
    )

    graph = GraphBuilder(framework=framework).build(catalog)
    edge = graph.get_edge("rel-related")
    assert edge is not None
    assert edge.directed is False
    assert edge.id in graph.outgoing[a.id]
    assert edge.id in graph.outgoing[b.id]
