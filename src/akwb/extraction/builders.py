"""Built-in candidate builders and validators for the extraction pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from akwb.extraction.models import ExtractionCandidate
from akwb.extraction.plugins import CandidateBuilder, CandidateValidator
from akwb.knowledge.models import (
    KnowledgeConfidence,
    KnowledgeEvidence,
    KnowledgeMetadata,
    KnowledgeObject,
    KnowledgeSource,
)
from akwb.knowledge.validation import ValidationResult
from akwb.types import Diagnostic

if TYPE_CHECKING:
    from akwb.extraction.pipeline import ExtractionContext


class DefaultKnowledgeObjectBuilder(CandidateBuilder):
    """Transform a validated extraction candidate into a canonical KnowledgeObject."""

    def build(
        self,
        candidate: ExtractionCandidate,
        source: KnowledgeSource,
        context: ExtractionContext | None = None,
    ) -> KnowledgeObject:
        artifact_source = candidate.source or source
        excerpt = candidate.evidence_excerpt or candidate.title
        location = candidate.evidence_location

        evidence = KnowledgeEvidence(
            source=artifact_source,
            type="extraction",
            excerpt=excerpt,
            location=location,
            extracted_by="akwb.extraction",
        )

        confidence = KnowledgeConfidence(
            value=candidate.confidence,
            method="algorithm",
        )

        metadata = KnowledgeMetadata(custom=candidate.metadata)
        if context and context.project_id:
            metadata.project_id = context.project_id

        return KnowledgeObject(
            type=candidate.knowledge_type,
            title=candidate.title,
            description=candidate.description,
            content=candidate.content,
            sources=[artifact_source],
            evidence=[evidence],
            domain_tags=candidate.tags,
            confidence=confidence,
            metadata=metadata,
        )


class RequiredFieldsCandidateValidator(CandidateValidator):
    """Ensure a candidate has the minimal fields required for building."""

    def validate(
        self,
        candidate: ExtractionCandidate,
        context: ExtractionContext | None = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        if not candidate.title or not candidate.title.strip():
            diagnostics.append(
                Diagnostic("error", "missing_title", "Candidate title is required")
            )
        if not candidate.knowledge_type or not candidate.knowledge_type.strip():
            diagnostics.append(
                Diagnostic("error", "missing_knowledge_type", "Candidate knowledge_type is required")
            )
        if diagnostics:
            return ValidationResult.failure(diagnostics)
        return ValidationResult.success()


class RegisteredTypeCandidateValidator(CandidateValidator):
    """Ensure the candidate's knowledge type is registered in the framework."""

    def validate(
        self,
        candidate: ExtractionCandidate,
        context: ExtractionContext | None = None,
    ) -> ValidationResult:
        if context is None or context.framework is None:
            return ValidationResult.success()
        if not context.framework.type_registry.has(candidate.knowledge_type):
            return ValidationResult.failure(
                [
                    Diagnostic(
                        "error",
                        "unknown_knowledge_type",
                        f"Knowledge type {candidate.knowledge_type!r} is not registered",
                    )
                ]
            )
        return ValidationResult.success()
