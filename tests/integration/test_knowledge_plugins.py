"""Integration tests for plugin-extensible knowledge framework."""

from __future__ import annotations

from pathlib import Path

import pytest

from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeEvidence,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
)
from akwb.plugins.registry import PluginRegistry


@pytest.fixture
def knowledge_plugin_dir() -> Path:
    return Path(__file__).parent.parent / "fixtures" / "knowledge_plugin"


def test_knowledge_plugin_extends_types_and_validators(knowledge_plugin_dir: Path) -> None:
    plugin_registry = PluginRegistry()
    result = plugin_registry.load_from_directory(knowledge_plugin_dir)
    assert result.ok, result.error

    framework = KnowledgeFramework()
    assert not framework.type_registry.has("custom_issue")

    framework.load_plugins(plugin_registry)

    assert framework.type_registry.has("custom_issue")
    assert framework.relationship_type_registry.has("custom_depends")
    assert framework.evidence_type_registry.has("custom_proof")

    # Built-ins remain available alongside plugin contributions.
    assert framework.type_registry.has("decision")
    assert framework.relationship_type_registry.has("depends_on")


def test_knowledge_plugin_validator_runs(knowledge_plugin_dir: Path) -> None:
    plugin_registry = PluginRegistry()
    plugin_registry.load_from_directory(knowledge_plugin_dir)

    framework = KnowledgeFramework()
    framework.load_plugins(plugin_registry)

    source = KnowledgeSource(kind="markdown", uri="test.md")
    evidence = KnowledgeEvidence(source=source, type="citation", excerpt="x")
    good = KnowledgeObject(
        type="decision",
        title="Use Postgres",
        sources=[source],
        evidence=[evidence],
    )
    bad = KnowledgeObject(
        type="decision",
        title="use Postgres",
        sources=[source],
        evidence=[evidence],
    )

    assert framework.validate_object(good).ok
    result = framework.validate_object(bad)
    assert not result.ok
    assert any("bad_title" in d.code for d in result.diagnostics)


def test_custom_relationship_type_validation(knowledge_plugin_dir: Path) -> None:
    plugin_registry = PluginRegistry()
    plugin_registry.load_from_directory(knowledge_plugin_dir)

    framework = KnowledgeFramework()
    framework.load_plugins(plugin_registry)

    source = KnowledgeSource(kind="markdown", uri="test.md")
    parent = KnowledgeObject(
        type="decision",
        title="Parent",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="x")],
    )
    child = KnowledgeObject(
        type="task",
        title="Child",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="x")],
    )
    catalog = framework.new_catalog()
    catalog.add_object(parent)
    catalog.add_object(child)

    rel = KnowledgeRelationship(
        relationship_type="custom_depends",
        from_ref=KnowledgeReference(ref=parent.id),
        to_ref=KnowledgeReference(ref=child.id),
    )
    catalog.add_relationship(rel)

    result = framework.validate_relationship(rel, catalog=catalog)
    assert result.ok
