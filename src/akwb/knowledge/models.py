"""Canonical domain models for the Enterprise Knowledge Object Framework."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from akwb.types import make_id, utc_now


class LifecycleState(str, Enum):
    """Allowed lifecycle states for a knowledge object."""

    DRAFT = "draft"
    PUBLISHED = "published"
    UPDATED = "updated"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ReferenceKind(str, Enum):
    """Kinds of references that can participate in relationships or evidence."""

    KNOWLEDGE_OBJECT = "knowledge_object"
    SOURCE = "source"
    EXTERNAL = "external"


class ConfidenceMethod:
    """Namespace for confidence-scoring method identifiers.

    Plugins may introduce additional methods; these are the built-in defaults.
    """

    MANUAL = "manual"
    AI = "ai"
    ALGORITHM = "algorithm"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class KnowledgeReference(BaseModel):
    """A portable pointer to another knowledge object or external source."""

    model_config = ConfigDict(frozen=True)

    ref: str = Field(..., description="Target identifier or URI.")
    kind: ReferenceKind = Field(
        default=ReferenceKind.KNOWLEDGE_OBJECT,
        description="Whether the reference points to a knowledge object or a source.",
    )
    label: str | None = Field(default=None, description="Human-readable label for the reference.")
    version: str | None = Field(default=None, description="Optional target version identifier.")


class KnowledgeSource(BaseModel):
    """A source from which a piece of knowledge was extracted or derived."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=make_id, description="Stable source identifier.")
    kind: str = Field(
        ...,
        description="Source kind (e.g. markdown, docx, pdf, code, image, email, chatgpt, claude, gemini).",
    )
    uri: str = Field(..., description="Location of the source (path, URL, or identifier).")
    mime_type: str | None = Field(default=None, description="MIME type when known.")
    digest: str | None = Field(default=None, description="Content hash for change detection.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra source metadata.")

    @field_validator("kind", "uri")
    @classmethod
    def _non_empty_strings(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("kind and uri must be non-empty strings")
        return value


class KnowledgeConfidence(BaseModel):
    """A confidence score together with provenance for the score."""

    model_config = ConfigDict(frozen=True)

    value: float = Field(..., ge=0.0, le=1.0, description="Confidence in [0.0, 1.0].")
    method: str = Field(
        default=ConfidenceMethod.UNKNOWN,
        description="Method used to derive the confidence value.",
    )
    timestamp: str = Field(default_factory=utc_now, description="When the confidence was recorded.")
    rationale: str | None = Field(default=None, description="Explanation for the confidence value.")


class KnowledgeVersion(BaseModel):
    """Versioning metadata for a knowledge object."""

    model_config = ConfigDict(frozen=True)

    state: LifecycleState = Field(
        default=LifecycleState.DRAFT,
        description="Current lifecycle state of this version.",
    )
    version: str = Field(default="1", description="Opaque version identifier.")
    previous_version_id: str | None = Field(
        default=None,
        description="Identifier of the immediately preceding version.",
    )
    superseded_by_id: str | None = Field(
        default=None,
        description="Identifier of the version that superseded this one.",
    )
    created_at: str = Field(default_factory=utc_now, description="Version creation timestamp.")
    published_at: str | None = Field(default=None, description="When the version was published.")
    archived_at: str | None = Field(default=None, description="When the version was archived.")


class LifecycleTransition(BaseModel):
    """A single lifecycle state transition."""

    model_config = ConfigDict(frozen=True)

    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: str = Field(default_factory=utc_now)
    actor: str | None = Field(default=None, description="Plugin, user, or process that performed the transition.")


class KnowledgeLifecycle(BaseModel):
    """Lifecycle state machine for a knowledge object."""

    model_config = ConfigDict(frozen=True)

    state: LifecycleState = Field(default=LifecycleState.DRAFT)
    history: list[LifecycleTransition] = Field(default_factory=list)

    # Valid state transitions.  An empty set means the state is terminal.
    _allowed: dict[LifecycleState, set[LifecycleState]] = {
        LifecycleState.DRAFT: {LifecycleState.PUBLISHED},
        LifecycleState.PUBLISHED: {
            LifecycleState.UPDATED,
            LifecycleState.SUPERSEDED,
            LifecycleState.ARCHIVED,
        },
        LifecycleState.UPDATED: {
            LifecycleState.PUBLISHED,
            LifecycleState.SUPERSEDED,
            LifecycleState.ARCHIVED,
        },
        LifecycleState.SUPERSEDED: {LifecycleState.ARCHIVED},
        LifecycleState.ARCHIVED: set(),
    }

    def transition(self, new_state: LifecycleState, actor: str | None = None) -> KnowledgeLifecycle:
        """Return a new lifecycle after validating and recording the transition."""
        if new_state == self.state:
            return self
        allowed = self._allowed.get(self.state, set())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid lifecycle transition from {self.state.value} to {new_state.value}"
            )
        transition = LifecycleTransition(
            from_state=self.state,
            to_state=new_state,
            actor=actor,
        )
        new_history = list(self.history)
        new_history.append(transition)
        return KnowledgeLifecycle(state=new_state, history=new_history)


class KnowledgeMetadata(BaseModel):
    """Contextual metadata attached to a knowledge object or relationship."""

    schema_version: str = Field(default="knowledge-v1")
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    created_by: str | None = Field(default=None)
    updated_by: str | None = Field(default=None)
    project_id: str | None = Field(default=None)
    domain: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class EvidenceType(BaseModel):
    """A kind of evidence (e.g. citation, quotation, AI extraction)."""

    id: str = Field(..., description="Machine-readable evidence type identifier.")
    name: str = Field(..., description="Human-readable name.")
    description: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeEvidence(BaseModel):
    """Evidence linking a knowledge claim to a source and optional location."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=make_id)
    source: KnowledgeSource
    type: str = Field(..., description="Evidence type identifier (e.g. citation, ai_extraction).")
    location: str | None = Field(
        default=None,
        description="Line number, page, timestamp, anchor, or other locator within the source.",
    )
    excerpt: str | None = Field(
        default=None,
        description="Relevant excerpt from the source supporting the knowledge.",
    )
    confidence: KnowledgeConfidence = Field(default_factory=lambda: KnowledgeConfidence(value=1.0))
    timestamp: str = Field(default_factory=utc_now)
    extracted_by: str | None = Field(default=None, description="Plugin or process that created the evidence.")

    @model_validator(mode="after")
    def _require_excerpt_or_location(self) -> KnowledgeEvidence:
        if self.excerpt is None and self.location is None:
            raise ValueError("Evidence must contain an excerpt, a location, or both.")
        return self


class KnowledgeType(BaseModel):
    """Plugin-contributable definition of a class of knowledge objects."""

    id: str = Field(..., description="Stable reverse-DNS or namespaced identifier.")
    name: str
    category: str | None = Field(default=None)
    description: str | None = Field(default=None)
    parent: str | None = Field(default=None, description="Optional parent knowledge type id.")
    content_schema: dict[str, Any] | None = Field(
        default=None,
        description="Optional structural schema for validating content.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipType(BaseModel):
    """Plugin-contributable definition of a relationship between knowledge objects."""

    id: str = Field(..., description="Stable relationship type identifier.")
    name: str
    directed: bool = Field(default=True)
    description: str | None = Field(default=None)
    allowed_from_types: list[str] | None = Field(
        default=None,
        description="If set, restricts source object knowledge types.",
    )
    allowed_to_types: list[str] | None = Field(
        default=None,
        description="If set, restricts target object knowledge types.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeRelationship(BaseModel):
    """A typed relationship between two knowledge references."""

    id: str = Field(default_factory=make_id)
    relationship_type: str = Field(..., description="Relationship type identifier.")
    from_ref: KnowledgeReference
    to_ref: KnowledgeReference
    evidence: list[KnowledgeEvidence] = Field(default_factory=list)
    confidence: KnowledgeConfidence = Field(default_factory=lambda: KnowledgeConfidence(value=1.0))
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)


class KnowledgeObject(BaseModel):
    """The canonical unit of project knowledge in AKWB."""

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: f"ku://{make_id()}")
    type: str = Field(..., description="Knowledge type identifier.")
    title: str = Field(..., min_length=1)
    description: str | None = Field(default=None)
    content: Any = Field(default=None, description="Structured or free-form content.")
    sources: list[KnowledgeSource] = Field(default_factory=list)
    evidence: list[KnowledgeEvidence] = Field(default_factory=list)
    references: list[KnowledgeReference] = Field(default_factory=list)
    metadata: KnowledgeMetadata = Field(default_factory=KnowledgeMetadata)
    version: KnowledgeVersion = Field(default_factory=KnowledgeVersion)
    lifecycle: KnowledgeLifecycle = Field(default_factory=KnowledgeLifecycle)
    confidence: KnowledgeConfidence = Field(default_factory=lambda: KnowledgeConfidence(value=1.0))
    domain_tags: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @property
    def primary_source(self) -> KnowledgeSource | None:
        """Return the first registered source, or None."""
        return self.sources[0] if self.sources else None

    def add_evidence(self, evidence: KnowledgeEvidence) -> None:
        """Append evidence and refresh the updated timestamp."""
        self.evidence.append(evidence)
        self.metadata.updated_at = utc_now()

    def transition_lifecycle(self, new_state: LifecycleState, actor: str | None = None) -> None:
        """Transition the object to a new lifecycle state."""
        self.lifecycle = self.lifecycle.transition(new_state, actor=actor)
        self.metadata.updated_at = utc_now()

    def references_object(self, target_id: str) -> bool:
        """Return True if this object references ``target_id``."""
        return any(
            ref.kind == ReferenceKind.KNOWLEDGE_OBJECT and ref.ref == target_id
            for ref in self.references
        )


class KnowledgeCatalog(BaseModel):
    """Aggregate of knowledge objects, relationships, and explicit type definitions."""

    schema_version: str = "knowledge-catalog-v1"
    metadata: dict[str, Any] = Field(default_factory=dict)
    objects: dict[str, KnowledgeObject] = Field(default_factory=dict)
    relationships: dict[str, KnowledgeRelationship] = Field(default_factory=dict)
    types: dict[str, KnowledgeType] = Field(default_factory=dict)
    relationship_types: dict[str, RelationshipType] = Field(default_factory=dict)
    evidence_types: dict[str, EvidenceType] = Field(default_factory=dict)

    model_config = ConfigDict(validate_assignment=True)

    def add_object(self, obj: KnowledgeObject) -> None:
        """Add a knowledge object, enforcing id uniqueness."""
        if obj.id in self.objects:
            raise ValueError(f"Knowledge object with id {obj.id!r} already exists")
        self.objects[obj.id] = obj

    def get_object(self, object_id: str) -> KnowledgeObject | None:
        """Return a knowledge object by id, or None."""
        return self.objects.get(object_id)

    def add_relationship(self, relationship: KnowledgeRelationship) -> None:
        """Add a relationship, enforcing id uniqueness."""
        if relationship.id in self.relationships:
            raise ValueError(f"Relationship with id {relationship.id!r} already exists")
        self.relationships[relationship.id] = relationship

    def get_relationships_for(
        self,
        ref: str | KnowledgeReference,
        direction: str = "both",
    ) -> list[KnowledgeRelationship]:
        """Return relationships where ``ref`` appears as source, target, or either.

        ``direction`` may be ``outgoing``, ``incoming``, or ``both``.
        """
        target_ref = ref.ref if isinstance(ref, KnowledgeReference) else ref
        results: list[KnowledgeRelationship] = []
        for rel in self.relationships.values():
            from_match = rel.from_ref.ref == target_ref
            to_match = rel.to_ref.ref == target_ref
            if direction == "outgoing" and from_match or direction == "incoming" and to_match or direction == "both" and (from_match or to_match):
                results.append(rel)
        return results

    def object_count(self) -> int:
        return len(self.objects)

    def relationship_count(self) -> int:
        return len(self.relationships)
