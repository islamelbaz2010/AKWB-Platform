"""Shared fixtures for graph engine tests."""

import pytest

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


@pytest.fixture
def sample_catalog() -> KnowledgeCatalog:
    """Return a catalog with three objects and two relationships."""
    framework = KnowledgeFramework()
    catalog = framework.new_catalog()

    decision = KnowledgeObject(
        id="ku://decision-1",
        type="decision",
        title="Use PostgreSQL",
        domain_tags=["database"],
        metadata={"project_id": "akwb", "domain": "engineering"},
    )
    technology = KnowledgeObject(
        id="ku://tech-1",
        type="technology",
        title="PostgreSQL",
        domain_tags=["database"],
        metadata={"project_id": "akwb", "domain": "engineering"},
    )
    requirement = KnowledgeObject(
        id="ku://req-1",
        type="requirement",
        title="High Availability",
        domain_tags=["sre"],
        metadata={"project_id": "akwb", "domain": "engineering"},
    )

    catalog.add_object(decision)
    catalog.add_object(technology)
    catalog.add_object(requirement)

    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-1",
            relationship_type="depends_on",
            from_ref=_ref(decision.id),
            to_ref=_ref(technology.id),
        )
    )
    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-2",
            relationship_type="depends_on",
            from_ref=_ref(requirement.id),
            to_ref=_ref(decision.id),
        )
    )

    return catalog


@pytest.fixture
def cyclic_catalog() -> KnowledgeCatalog:
    """Return a catalog with a directed cycle."""
    framework = KnowledgeFramework()
    catalog = framework.new_catalog()

    a = KnowledgeObject(
        id="ku://a",
        type="component",
        title="Service A",
        metadata={"project_id": "akwb"},
    )
    b = KnowledgeObject(
        id="ku://b",
        type="component",
        title="Service B",
        metadata={"project_id": "akwb"},
    )
    c = KnowledgeObject(
        id="ku://c",
        type="component",
        title="Service C",
        metadata={"project_id": "akwb"},
    )

    catalog.add_object(a)
    catalog.add_object(b)
    catalog.add_object(c)

    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-a-b",
            relationship_type="depends_on",
            from_ref=_ref(a.id),
            to_ref=_ref(b.id),
        )
    )
    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-b-c",
            relationship_type="depends_on",
            from_ref=_ref(b.id),
            to_ref=_ref(c.id),
        )
    )
    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-c-a",
            relationship_type="depends_on",
            from_ref=_ref(c.id),
            to_ref=_ref(a.id),
        )
    )

    return catalog
