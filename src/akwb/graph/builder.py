"""Build a KnowledgeGraph from a KnowledgeCatalog."""

from __future__ import annotations

from typing import Any

from akwb.graph.models import KnowledgeGraph
from akwb.knowledge.models import (
    KnowledgeCatalog,
    ReferenceKind,
    RelationshipType,
)


class GraphBuilder:
    """Construct a canonical KnowledgeGraph from a KnowledgeCatalog."""

    def __init__(self, framework: Any | None = None) -> None:
        self.framework = framework

    def build(self, catalog: KnowledgeCatalog) -> KnowledgeGraph:
        """Return a KnowledgeGraph representing ``catalog``."""
        graph = KnowledgeGraph(
            metadata={
                "catalog_id": catalog.metadata.get("id"),
                "object_count": catalog.object_count(),
                "relationship_count": catalog.relationship_count(),
            }
        )

        for obj in catalog.objects.values():
            graph.add_node(obj)

        for relationship in catalog.relationships.values():
            directed = self._is_directed(
                relationship.relationship_type,
                catalog,
            )
            graph.add_edge(relationship, directed=directed)

        # Add synthetic edges for object references of kind KNOWLEDGE_OBJECT.
        for obj in catalog.objects.values():
            for ref in obj.references:
                if ref.kind == ReferenceKind.KNOWLEDGE_OBJECT:
                    directed = self._is_directed("references", catalog)
                    graph.add_reference_edge(
                        obj.id,
                        ref.ref,
                        relationship_type="references",
                        directed=directed,
                    )

        return graph

    def _is_directed(
        self,
        relationship_type: str,
        catalog: KnowledgeCatalog,
    ) -> bool:
        relationship_def = self._lookup_relationship_type(
            relationship_type,
            catalog,
        )
        if relationship_def is not None:
            return relationship_def.directed
        return True

    def _lookup_relationship_type(
        self,
        relationship_type: str,
        catalog: KnowledgeCatalog,
    ) -> RelationshipType | None:
        if relationship_type in catalog.relationship_types:
            return catalog.relationship_types[relationship_type]
        if self.framework is not None:
            rel = self.framework.relationship_type_registry.get(relationship_type)
            if isinstance(rel, RelationshipType):
                return rel
        return None
