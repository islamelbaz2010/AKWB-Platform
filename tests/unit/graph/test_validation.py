"""Tests for graph validation."""

from akwb.graph.builder import GraphBuilder
from akwb.graph.models import KnowledgeGraph
from akwb.graph.validation import GraphValidator
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    ReferenceKind,
)


def _ref(obj_id: str) -> KnowledgeReference:
    return KnowledgeReference(kind=ReferenceKind.KNOWLEDGE_OBJECT, ref=obj_id)


def test_valid_graph(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    validator = GraphValidator(framework=KnowledgeFramework())
    result = validator.validate(graph)
    assert result.ok


def test_broken_reference(sample_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(sample_catalog)
    graph.add_edge(
        KnowledgeRelationship(
            id="broken",
            relationship_type="depends_on",
            from_ref=_ref("ku://decision-1"),
            to_ref=_ref("ku://missing"),
        )
    )

    validator = GraphValidator()
    result = validator.validate(graph)
    assert not result.ok
    assert any("broken_reference" in d.code for d in result.diagnostics)


def test_cycle_detection(cyclic_catalog: KnowledgeCatalog) -> None:
    graph = GraphBuilder().build(cyclic_catalog)
    validator = GraphValidator()
    result = validator.validate(graph)
    assert not result.ok
    assert any("cycle" in d.code for d in result.diagnostics)


def test_orphan_node_warning() -> None:
    graph = KnowledgeGraph()
    graph.add_node(KnowledgeObject(id="ku://orphan", type="decision", title="Orphan"))
    result = GraphValidator().validate(graph)
    assert any("orphan_node" in d.code for d in result.diagnostics)


def test_invalid_relationship_type() -> None:
    graph = KnowledgeGraph()
    a = KnowledgeObject(id="ku://a", type="component", title="A")
    b = KnowledgeObject(id="ku://b", type="component", title="B")
    graph.add_node(a)
    graph.add_node(b)
    graph.add_edge(
        KnowledgeRelationship(
            id="bad",
            relationship_type="not_a_type",
            from_ref=_ref(a.id),
            to_ref=_ref(b.id),
        )
    )

    validator = GraphValidator(framework=KnowledgeFramework())
    result = validator.validate(graph)
    assert not result.ok
    assert any("invalid_relationship_type" in d.code for d in result.diagnostics)
