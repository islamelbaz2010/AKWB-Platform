"""Shared fixtures for graph integration tests."""

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
