"""Unit tests for knowledge framework domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from akwb.knowledge.models import (
    ConfidenceMethod,
    KnowledgeCatalog,
    KnowledgeConfidence,
    KnowledgeEvidence,
    KnowledgeLifecycle,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
    KnowledgeType,
    KnowledgeVersion,
    LifecycleState,
    ReferenceKind,
)


def test_knowledge_source_requires_kind_and_uri() -> None:
    with pytest.raises(ValidationError):
        KnowledgeSource(kind="", uri="")

    source = KnowledgeSource(kind="markdown", uri="docs/readme.md")
    assert source.kind == "markdown"
    assert source.uri == "docs/readme.md"


def test_knowledge_confidence_range() -> None:
    with pytest.raises(ValidationError):
        KnowledgeConfidence(value=1.5)

    confidence = KnowledgeConfidence(value=0.85, method=ConfidenceMethod.AI)
    assert confidence.value == 0.85
    assert confidence.method == ConfidenceMethod.AI


def test_knowledge_object_minimal() -> None:
    obj = KnowledgeObject(type="decision", title="Use PostgreSQL")
    assert obj.type == "decision"
    assert obj.title == "Use PostgreSQL"
    assert obj.id.startswith("ku://")
    assert obj.lifecycle.state == LifecycleState.DRAFT


def test_knowledge_object_requires_title() -> None:
    with pytest.raises(ValidationError):
        KnowledgeObject(type="requirement", title="")


def test_evidence_requires_excerpt_or_location() -> None:
    source = KnowledgeSource(kind="markdown", uri="adr/001.md")
    with pytest.raises(ValidationError):
        KnowledgeEvidence(source=source, type="citation")

    evidence = KnowledgeEvidence(source=source, type="citation", excerpt="foo")
    assert evidence.excerpt == "foo"


def test_lifecycle_transitions() -> None:
    lifecycle = KnowledgeLifecycle()
    assert lifecycle.state == LifecycleState.DRAFT

    published = lifecycle.transition(LifecycleState.PUBLISHED, actor="user")
    assert published.state == LifecycleState.PUBLISHED
    assert len(published.history) == 1

    archived = published.transition(LifecycleState.ARCHIVED)
    assert archived.state == LifecycleState.ARCHIVED

    with pytest.raises(ValueError):
        lifecycle.transition(LifecycleState.ARCHIVED)


def test_knowledge_object_lifecycle_transition() -> None:
    obj = KnowledgeObject(type="risk", title="Data loss")
    obj.transition_lifecycle(LifecycleState.PUBLISHED, actor="framework")
    assert obj.lifecycle.state == LifecycleState.PUBLISHED
    assert obj.version.state == LifecycleState.DRAFT  # version metadata is independent


def test_knowledge_catalog_add_and_retrieve() -> None:
    catalog = KnowledgeCatalog()
    obj = KnowledgeObject(type="goal", title="Ship v1")
    catalog.add_object(obj)
    assert catalog.get_object(obj.id) is obj
    assert catalog.object_count() == 1

    with pytest.raises(ValueError):
        catalog.add_object(obj)


def test_relationship_lookup() -> None:
    catalog = KnowledgeCatalog()
    parent = KnowledgeObject(type="goal", title="Parent")
    child = KnowledgeObject(type="task", title="Child")
    catalog.add_object(parent)
    catalog.add_object(child)

    rel = KnowledgeRelationship(
        relationship_type="contains",
        from_ref=KnowledgeReference(ref=parent.id),
        to_ref=KnowledgeReference(ref=child.id),
    )
    catalog.add_relationship(rel)

    assert len(catalog.get_relationships_for(parent.id, "outgoing")) == 1
    assert len(catalog.get_relationships_for(child.id, "incoming")) == 1
    assert len(catalog.get_relationships_for(parent.id, "both")) == 1


def test_reference_kind_enum() -> None:
    ref = KnowledgeReference(ref="ku://abc", kind=ReferenceKind.SOURCE)
    assert ref.kind == ReferenceKind.SOURCE
    assert ref.kind.value == "source"


def test_knowledge_type_content_schema() -> None:
    schema = {
        "required": ["status"],
        "properties": {"status": {"type": "string"}},
    }
    kt = KnowledgeType(id="custom", name="Custom", content_schema=schema)
    assert kt.content_schema == schema


def test_version_state_defaults() -> None:
    version = KnowledgeVersion()
    assert version.state == LifecycleState.DRAFT
    assert version.version == "1"
