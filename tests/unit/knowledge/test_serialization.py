"""Tests for JSON, JSONL, and YAML serialization of knowledge objects and catalogs."""

from __future__ import annotations

import pytest

from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeEvidence,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
)
from akwb.knowledge.serialization import (
    JsonlSerializer,
    SerializationFormat,
    YamlSerializer,
)


def _sample_catalog() -> KnowledgeCatalog:
    catalog = KnowledgeCatalog()
    source = KnowledgeSource(kind="markdown", uri="docs/adr.md")
    obj = KnowledgeObject(
        type="decision",
        title="Use Postgres",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="We chose Postgres.")],
    )
    catalog.add_object(obj)

    child = KnowledgeObject(
        type="task",
        title="Create schema",
        sources=[source],
        evidence=[KnowledgeEvidence(source=source, type="citation", excerpt="Schema needed.")],
    )
    catalog.add_object(child)

    rel = KnowledgeRelationship(
        relationship_type="contains",
        from_ref=KnowledgeReference(ref=obj.id),
        to_ref=KnowledgeReference(ref=child.id),
    )
    catalog.add_relationship(rel)
    return catalog


@pytest.mark.parametrize("fmt", [SerializationFormat.JSON, SerializationFormat.YAML])
def test_catalog_roundtrip(fmt: str) -> None:
    framework = KnowledgeFramework()
    catalog = _sample_catalog()
    serialized = framework.serialize_catalog(catalog, fmt=fmt)
    assert isinstance(serialized, str)
    assert "Use Postgres" in serialized

    restored = framework.deserialize_catalog(serialized, fmt=fmt)
    assert restored.object_count() == catalog.object_count()
    assert restored.relationship_count() == catalog.relationship_count()
    restored_obj = restored.objects[next(iter(catalog.objects.keys()))]
    assert restored_obj.title == "Use Postgres"
    assert restored_obj.sources[0].kind == "markdown"


def test_jsonl_catalog_roundtrip() -> None:
    framework = KnowledgeFramework()
    catalog = _sample_catalog()
    serialized = framework.serialize_catalog(catalog, fmt=SerializationFormat.JSONL)
    assert serialized.count("\n") >= 2
    assert "KnowledgeObject" in serialized

    restored = framework.deserialize_catalog(serialized, fmt=SerializationFormat.JSONL)
    assert restored.object_count() == 2
    assert restored.relationship_count() == 1


def test_object_json_roundtrip() -> None:
    framework = KnowledgeFramework()
    obj = KnowledgeObject(
        type="requirement",
        title="REST API",
        sources=[KnowledgeSource(kind="markdown", uri="req.md")],
        evidence=[KnowledgeEvidence(
            source=KnowledgeSource(kind="markdown", uri="req.md"),
            type="quotation",
            excerpt="Must expose REST API",
        )],
    )
    data = framework.serialize_object(obj, fmt=SerializationFormat.JSON)
    restored = framework.deserialize_object(data, fmt=SerializationFormat.JSON)
    assert restored.title == "REST API"
    assert restored.type == "requirement"
    assert len(restored.evidence) == 1


def test_jsonl_object_roundtrip() -> None:
    serializer = JsonlSerializer()
    obj = KnowledgeObject(
        type="risk",
        title="Vendor lock-in",
        sources=[KnowledgeSource(kind="docx", uri="risk.docx")],
    )
    line = serializer.serialize_object(obj)
    restored = serializer.deserialize_object(line)
    assert restored.title == "Vendor lock-in"


def test_yaml_serializer_handles_metadata() -> None:
    catalog = _sample_catalog()
    catalog.metadata = {"project": "akwb"}
    serialized = YamlSerializer().serialize_catalog(catalog)
    restored = YamlSerializer().deserialize_catalog(serialized)
    assert restored.metadata == {"project": "akwb"}


def test_unknown_serializer_raises() -> None:
    framework = KnowledgeFramework()
    with pytest.raises(ValueError):
        framework.get_serializer("xml")
