"""Usage example for the Enterprise Knowledge Graph Engine."""

from __future__ import annotations

from akwb.graph.engine import GraphEngine
from akwb.graph.models import GraphQuery, TraversalRequest
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    ReferenceKind,
)


def _ref(obj_id: str) -> KnowledgeReference:
    return KnowledgeReference(kind=ReferenceKind.KNOWLEDGE_OBJECT, ref=obj_id)


def main() -> None:
    framework = KnowledgeFramework()
    catalog = framework.new_catalog()

    decision = KnowledgeObject(
        id="ku://adr-001",
        type="decision",
        title="Use PostgreSQL",
        domain_tags=["database", "architecture"],
        metadata={"project_id": "akwb", "domain": "engineering"},
    )
    technology = KnowledgeObject(
        id="ku://postgres",
        type="technology",
        title="PostgreSQL",
        domain_tags=["database"],
        metadata={"project_id": "akwb", "domain": "engineering"},
    )
    requirement = KnowledgeObject(
        id="ku://ha-001",
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
            id="rel-adr-db",
            relationship_type="depends_on",
            from_ref=_ref(decision.id),
            to_ref=_ref(technology.id),
        )
    )
    catalog.add_relationship(
        KnowledgeRelationship(
            id="rel-ha-adr",
            relationship_type="depends_on",
            from_ref=_ref(requirement.id),
            to_ref=_ref(decision.id),
        )
    )

    engine = GraphEngine(framework=framework)
    graph = engine.build(catalog)

    print(f"Nodes: {graph.node_count()}, Edges: {graph.edge_count()}")

    query = engine.query(graph, GraphQuery(node_type="decision"))
    print(f"Decision nodes: {query.node_ids}")

    traversal = engine.traverse(
        graph,
        TraversalRequest(start=requirement.id, strategy="dependency"),
    )
    print(f"Dependency walk from {requirement.id}: {traversal.node_ids}")

    shortest = engine.traverse(
        graph,
        TraversalRequest(
            start=requirement.id,
            target=technology.id,
            strategy="shortest",
        ),
    )
    print(f"Shortest path: {shortest.path}")

    validation = engine.validate(graph)
    print(f"Validation OK: {validation.ok}")

    stats = engine.statistics(graph)
    print(
        f"Stats: {stats.node_count} nodes, {stats.edge_count} edges, "
        f"{stats.connected_components} component(s), {stats.cycle_count} cycle(s)"
    )


if __name__ == "__main__":
    main()
