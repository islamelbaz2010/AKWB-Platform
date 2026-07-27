"""Tests for graph domain models."""

from akwb.graph.models import Direction, KnowledgeGraph
from akwb.knowledge.models import (
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    ReferenceKind,
)


def _ref(obj_id: str) -> KnowledgeReference:
    return KnowledgeReference(kind=ReferenceKind.KNOWLEDGE_OBJECT, ref=obj_id)


def test_knowledge_graph_adds_nodes_and_edges() -> None:
    graph = KnowledgeGraph()
    obj_a = KnowledgeObject(id="ku://a", type="decision", title="A")
    obj_b = KnowledgeObject(id="ku://b", type="technology", title="B")

    graph.add_node(obj_a)
    graph.add_node(obj_b)
    rel = KnowledgeRelationship(
        relationship_type="depends_on",
        from_ref=_ref("ku://a"),
        to_ref=_ref("ku://b"),
    )
    graph.add_edge(rel)

    assert graph.node_count() == 2
    assert graph.edge_count() == 1
    assert graph.get_outgoing_edges("ku://a")[0].target_id == "ku://b"
    assert graph.get_incoming_edges("ku://b")[0].source_id == "ku://a"


def test_neighbors_and_directions() -> None:
    graph = KnowledgeGraph()
    obj_a = KnowledgeObject(id="ku://a", type="decision", title="A")
    obj_b = KnowledgeObject(id="ku://b", type="technology", title="B")
    graph.add_node(obj_a)
    graph.add_node(obj_b)
    graph.add_edge(
        KnowledgeRelationship(
            relationship_type="depends_on",
            from_ref=_ref("ku://a"),
            to_ref=_ref("ku://b"),
        )
    )

    assert graph.neighbors("ku://a", direction=Direction.OUTGOING) == {"ku://b"}
    assert graph.neighbors("ku://b", direction=Direction.INCOMING) == {"ku://a"}
    assert graph.neighbors("ku://a") == {"ku://b"}


def test_descendants_and_ancestors() -> None:
    graph = KnowledgeGraph()
    ids = ["ku://a", "ku://b", "ku://c"]
    for oid in ids:
        graph.add_node(KnowledgeObject(id=oid, type="component", title=oid))

    graph.add_edge(
        KnowledgeRelationship(
            relationship_type="depends_on",
            from_ref=_ref("ku://a"),
            to_ref=_ref("ku://b"),
        )
    )
    graph.add_edge(
        KnowledgeRelationship(
            relationship_type="depends_on",
            from_ref=_ref("ku://b"),
            to_ref=_ref("ku://c"),
        )
    )

    assert graph.descendants("ku://a") == {"ku://b", "ku://c"}
    assert graph.ancestors("ku://c") == {"ku://a", "ku://b"}
    assert graph.shortest_path("ku://a", "ku://c") == ["ku://a", "ku://b", "ku://c"]


def test_connected_components() -> None:
    graph = KnowledgeGraph()
    for oid in ["ku://a", "ku://b", "ku://c", "ku://d"]:
        graph.add_node(KnowledgeObject(id=oid, type="component", title=oid))

    graph.add_edge(
        KnowledgeRelationship(
            relationship_type="related_to",
            from_ref=_ref("ku://a"),
            to_ref=_ref("ku://b"),
        ),
        directed=False,
    )
    graph.add_edge(
        KnowledgeRelationship(
            relationship_type="related_to",
            from_ref=_ref("ku://c"),
            to_ref=_ref("ku://d"),
        ),
        directed=False,
    )

    components = graph.connected_components()
    assert len(components) == 2
    assert {"ku://a", "ku://b"} in components
    assert {"ku://c", "ku://d"} in components
