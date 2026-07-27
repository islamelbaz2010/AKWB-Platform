"""Unit tests for the KnowledgeFramework orchestrator."""

from __future__ import annotations

from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeEvidence,
    KnowledgeLifecycle,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
    KnowledgeVersion,
    LifecycleState,
)


def test_framework_loads_builtins() -> None:
    framework = KnowledgeFramework()
    assert framework.type_registry.has("decision")
    assert framework.type_registry.has("risk")
    assert framework.relationship_type_registry.has("depends_on")
    assert framework.evidence_type_registry.has("citation")


def test_framework_validate_valid_object() -> None:
    framework = KnowledgeFramework()
    source = KnowledgeSource(kind="markdown", uri="docs/adr.md")
    evidence = KnowledgeEvidence(source=source, type="citation", excerpt="Pick Postgres.")
    obj = KnowledgeObject(
        type="decision",
        title="Database",
        sources=[source],
        evidence=[evidence],
    )
    result = framework.validate_object(obj)
    assert result.ok


def test_framework_validate_missing_traceability() -> None:
    framework = KnowledgeFramework()
    obj = KnowledgeObject(type="decision", title="Database")
    result = framework.validate_object(obj)
    assert not result.ok
    assert any("missing_traceability" in d.code for d in result.diagnostics)


def test_framework_validate_catalog() -> None:
    framework = KnowledgeFramework()
    catalog = KnowledgeCatalog()

    source = KnowledgeSource(kind="markdown", uri="docs/adr.md")
    parent = KnowledgeObject(
        type="goal",
        title="Ship v1",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="Goal.")],
    )
    child = KnowledgeObject(
        type="task",
        title="Build API",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="Task.")],
    )
    catalog.add_object(parent)
    catalog.add_object(child)

    rel = KnowledgeRelationship(
        relationship_type="contains",
        from_ref=KnowledgeReference(ref=parent.id),
        to_ref=KnowledgeReference(ref=child.id),
    )
    catalog.add_relationship(rel)

    result = framework.validate_catalog(catalog)
    assert result.ok, result.diagnostics


def test_new_catalog_contains_builtins() -> None:
    framework = KnowledgeFramework()
    catalog = framework.new_catalog(project="demo")
    assert catalog.types
    assert catalog.relationship_types
    assert catalog.evidence_types
    assert catalog.metadata["project"] == "demo"


def test_lifecycle_validator_in_framework() -> None:
    framework = KnowledgeFramework()
    source = KnowledgeSource(kind="markdown", uri="docs/adr.md")
    obj = KnowledgeObject(
        type="decision",
        title="DB",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="x")],
        lifecycle=KnowledgeLifecycle(state=LifecycleState.PUBLISHED),
        version=KnowledgeVersion(state=LifecycleState.DRAFT),
    )
    result = framework.validate_object(obj)
    assert not result.ok
    assert any("lifecycle_version_mismatch" in d.code for d in result.diagnostics)
