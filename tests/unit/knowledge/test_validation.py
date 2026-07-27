"""Tests for the knowledge framework validation framework."""

from __future__ import annotations

import pytest

from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeConfidence,
    KnowledgeEvidence,
    KnowledgeLifecycle,
    KnowledgeMetadata,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
    KnowledgeVersion,
    LifecycleState,
)
from akwb.knowledge.validation import (
    CompositeValidator,
    ConfidenceValidator,
    EvidenceValidator,
    LifecycleValidator,
    MetadataValidator,
    RelationshipValidator,
    TraceabilityValidator,
    TypeValidator,
    ValidationResult,
)


def _valid_object() -> KnowledgeObject:
    source = KnowledgeSource(kind="markdown", uri="docs/adr.md")
    evidence = KnowledgeEvidence(source=source, type="citation", excerpt="foo")
    return KnowledgeObject(
        type="decision",
        title="Use Postgres",
        sources=[source],
        evidence=[evidence],
    )


@pytest.fixture
def framework() -> KnowledgeFramework:
    return KnowledgeFramework()


def test_validation_result_merge() -> None:
    a = ValidationResult(ok=True)
    b = ValidationResult(ok=False, diagnostics=[])
    a.merge(b)
    assert a.ok is False


def test_type_validator_accepts_registered_type(framework: KnowledgeFramework) -> None:
    obj = _valid_object()
    result = TypeValidator().validate_object(obj, framework=framework)
    assert result.ok
    assert not result.diagnostics


def test_type_validator_rejects_unknown_type(framework: KnowledgeFramework) -> None:
    obj = _valid_object()
    obj.type = "unknown_xyz"
    result = TypeValidator().validate_object(obj, framework=framework)
    assert not result.ok
    assert any("unknown_knowledge_type" in d.code for d in result.diagnostics)


def test_type_validator_enforces_content_schema(framework: KnowledgeFramework) -> None:
    obj = _valid_object()
    # Register a type that requires a 'status' string field
    from akwb.knowledge.models import KnowledgeType
    from akwb.knowledge.registries import TypeRegistry

    registry = TypeRegistry[KnowledgeType]()
    registry.register(
        KnowledgeType(
            id="custom_ticket",
            name="Custom Ticket",
            content_schema={
                "required": ["status"],
                "properties": {"status": {"type": "string"}},
            },
        )
    )

    # Use a fresh framework to avoid tainting builtins registry.

    custom_framework = KnowledgeFramework()
    custom_framework.type_registry.register(
        KnowledgeType(
            id="custom_ticket",
            name="Custom Ticket",
            content_schema={
                "required": ["status"],
                "properties": {"status": {"type": "string"}},
            },
        )
    )

    obj.type = "custom_ticket"
    obj.content = {}
    result = TypeValidator().validate_object(obj, framework=custom_framework)
    assert not result.ok
    assert any("missing_required_field" in d.code for d in result.diagnostics)

    obj.content = {"status": "open"}
    result = TypeValidator().validate_object(obj, framework=custom_framework)
    assert result.ok

    obj.content = {"status": 123}
    result = TypeValidator().validate_object(obj, framework=custom_framework)
    assert not result.ok
    assert any("field_type_mismatch" in d.code for d in result.diagnostics)


def test_relationship_validator_accepts_valid(framework: KnowledgeFramework) -> None:
    catalog = KnowledgeCatalog()
    parent = _valid_object()
    child = _valid_object()
    child.title = "Child"
    catalog.add_object(parent)
    catalog.add_object(child)

    rel = KnowledgeRelationship(
        relationship_type="contains",
        from_ref=KnowledgeReference(ref=parent.id),
        to_ref=KnowledgeReference(ref=child.id),
    )
    result = RelationshipValidator().validate_relationship(rel, catalog=catalog, framework=framework)
    assert result.ok


def test_relationship_validator_rejects_unknown_type(framework: KnowledgeFramework) -> None:
    rel = KnowledgeRelationship(
        relationship_type="foo",
        from_ref=KnowledgeReference(ref="a"),
        to_ref=KnowledgeReference(ref="b"),
    )
    result = RelationshipValidator().validate_relationship(rel, framework=framework)
    assert not result.ok
    assert any("unknown_relationship_type" in d.code for d in result.diagnostics)


def test_relationship_validator_rejects_missing_endpoint(framework: KnowledgeFramework) -> None:
    catalog = KnowledgeCatalog()
    obj = _valid_object()
    catalog.add_object(obj)

    rel = KnowledgeRelationship(
        relationship_type="depends_on",
        from_ref=KnowledgeReference(ref=obj.id),
        to_ref=KnowledgeReference(ref="missing"),
    )
    result = RelationshipValidator().validate_relationship(rel, catalog=catalog, framework=framework)
    assert not result.ok
    assert any("missing_relationship_endpoint" in d.code for d in result.diagnostics)


def test_relationship_validator_type_constraints(framework: KnowledgeFramework) -> None:
    from akwb.knowledge.models import RelationshipType

    framework.relationship_type_registry.register(
        RelationshipType(
            id="implemented_by",
            name="Implemented By",
            allowed_from_types=["requirement"],
            allowed_to_types=["component"],
        )
    )
    catalog = KnowledgeCatalog()
    req = KnowledgeObject(type="requirement", title="R1", sources=[KnowledgeSource(kind="markdown", uri="r.md")])
    comp = KnowledgeObject(type="component", title="C1", sources=[KnowledgeSource(kind="markdown", uri="c.md")])
    catalog.add_object(req)
    catalog.add_object(comp)

    rel = KnowledgeRelationship(
        relationship_type="implemented_by",
        from_ref=KnowledgeReference(ref=req.id),
        to_ref=KnowledgeReference(ref=comp.id),
    )
    result = RelationshipValidator().validate_relationship(rel, catalog=catalog, framework=framework)
    assert result.ok

    bad = KnowledgeObject(type="decision", title="D1", sources=[KnowledgeSource(kind="markdown", uri="d.md")])
    catalog.add_object(bad)
    rel2 = KnowledgeRelationship(
        relationship_type="implemented_by",
        from_ref=KnowledgeReference(ref=bad.id),
        to_ref=KnowledgeReference(ref=comp.id),
    )
    result = RelationshipValidator().validate_relationship(rel2, catalog=catalog, framework=framework)
    assert not result.ok
    assert any("invalid_from_type" in d.code for d in result.diagnostics)


def test_evidence_validator_rejects_missing_source() -> None:
    obj = _valid_object()
    bad_source = KnowledgeSource.model_construct(kind="", uri="")
    obj.evidence = [KnowledgeEvidence.model_construct(source=bad_source, type="citation", excerpt="x")]
    result = EvidenceValidator().validate_object(obj)
    assert not result.ok
    assert any("missing_evidence_source_uri" in d.code for d in result.diagnostics)
    assert any("missing_evidence_source_kind" in d.code for d in result.diagnostics)


def test_traceability_validator_rejects_unsourced_object() -> None:
    obj = KnowledgeObject(type="decision", title="No trace")
    result = TraceabilityValidator().validate_object(obj)
    assert not result.ok
    assert any("missing_traceability" in d.code for d in result.diagnostics)


def test_metadata_validator_checks_required_fields() -> None:
    obj = _valid_object()
    obj.metadata.schema_version = ""
    result = MetadataValidator().validate_object(obj)
    assert not result.ok
    assert any("missing_schema_version" in d.code for d in result.diagnostics)

    obj.metadata = KnowledgeMetadata(schema_version="knowledge-v1")
    result = MetadataValidator().validate_object(obj)
    assert result.ok


def test_confidence_validator_checks_bounds() -> None:
    bad_confidence = KnowledgeConfidence.model_construct(value=1.5)
    obj = KnowledgeObject.model_construct(
        type="decision",
        title="T",
        sources=[KnowledgeSource(kind="markdown", uri="x.md")],
        evidence=[],
        confidence=bad_confidence,
    )
    result = ConfidenceValidator().validate_object(obj)
    assert not result.ok
    assert any("invalid_confidence" in d.code for d in result.diagnostics)

    obj = _valid_object()
    obj.confidence = KnowledgeConfidence(value=0.5)
    result = ConfidenceValidator().validate_object(obj)
    assert result.ok


def test_lifecycle_validator_catches_mismatch() -> None:
    obj = _valid_object()
    obj.lifecycle = KnowledgeLifecycle(state=LifecycleState.PUBLISHED)
    obj.version = KnowledgeVersion(state=LifecycleState.DRAFT)
    result = LifecycleValidator().validate_object(obj)
    assert not result.ok
    assert any("lifecycle_version_mismatch" in d.code for d in result.diagnostics)


def test_lifecycle_validator_warns_archived_without_at() -> None:
    obj = _valid_object()
    obj.lifecycle = KnowledgeLifecycle(state=LifecycleState.ARCHIVED)
    obj.version = KnowledgeVersion(state=LifecycleState.ARCHIVED)
    result = LifecycleValidator().validate_object(obj)
    assert result.ok
    assert any("missing_archived_at" in d.code for d in result.diagnostics)
    assert all(d.level != "error" for d in result.diagnostics)


def test_composite_validator_runs_all(framework: KnowledgeFramework) -> None:
    obj = _valid_object()
    validators = [TypeValidator(), EvidenceValidator(), TraceabilityValidator(), MetadataValidator()]
    result = CompositeValidator(validators).validate_object(obj, framework=framework)
    assert result.ok

    obj.type = "unknown"
    result = CompositeValidator(validators).validate_object(obj, framework=framework)
    assert not result.ok
