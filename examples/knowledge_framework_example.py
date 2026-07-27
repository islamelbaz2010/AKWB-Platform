"""Usage example for the AKWB Enterprise Knowledge Object Framework."""

from __future__ import annotations

from akwb.knowledge import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeEvidence,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
    LifecycleState,
)


def main() -> None:
    framework = KnowledgeFramework()
    catalog = framework.new_catalog(project="akwb", team="platform")

    source = KnowledgeSource(
        kind="markdown",
        uri="docs/adr/001-postgresql.md",
        mime_type="text/markdown",
    )
    evidence = KnowledgeEvidence(
        source=source,
        type="citation",
        location="lines 12-18",
        excerpt="We will adopt PostgreSQL for the primary data store.",
    )

    adr = KnowledgeObject(
        type="decision",
        title="Adopt PostgreSQL",
        description="Record the decision to use PostgreSQL for relational storage.",
        sources=[source],
        evidence=[evidence],
        domain_tags=["architecture", "database"],
    )
    catalog.add_object(adr)

    schema_task = KnowledgeObject(
        type="task",
        title="Design database schema",
        sources=[source],
        evidence=[evidence],
        domain_tags=["architecture"],
    )
    catalog.add_object(schema_task)

    rel = KnowledgeRelationship(
        relationship_type="contains",
        from_ref=KnowledgeReference(ref=adr.id),
        to_ref=KnowledgeReference(ref=schema_task.id),
        evidence=[evidence],
    )
    catalog.add_relationship(rel)

    print(f"Catalog: {catalog.object_count()} objects, {catalog.relationship_count()} relationships")

    validation = framework.validate_catalog(catalog)
    print(f"Validation: {'OK' if validation.ok else 'FAILED'}")
    if not validation.ok:
        for diag in validation.diagnostics:
            print(f"  - {diag}")

    json_output = framework.serialize_catalog(catalog, fmt="json")
    print("\n--- JSON output (first 500 bytes) ---")
    print(json_output[:500])

    adr.transition_lifecycle(LifecycleState.PUBLISHED, actor="user")
    print(f"\nADR lifecycle: {adr.lifecycle.state.value}")


if __name__ == "__main__":
    main()
