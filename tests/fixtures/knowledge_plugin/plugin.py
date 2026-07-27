"""Sample plugin for knowledge framework integration tests."""

from __future__ import annotations

from akwb.knowledge.models import EvidenceType, KnowledgeType, RelationshipType
from akwb.knowledge.plugins import (
    EvidenceTypeProvider,
    KnowledgeTypeProvider,
    KnowledgeValidatorProvider,
    RelationshipTypeProvider,
)
from akwb.knowledge.validation import KnowledgeValidator, ValidationResult
from akwb.types import Diagnostic


class TestTypeProvider(KnowledgeTypeProvider):
    """Contributes a custom knowledge type."""

    def get_types(self) -> list[KnowledgeType]:
        return [KnowledgeType(id="custom_issue", name="Custom Issue", category="test")]


class TestRelationshipProvider(RelationshipTypeProvider):
    """Contributes a custom relationship type."""

    def get_relationship_types(self) -> list[RelationshipType]:
        return [RelationshipType(id="custom_depends", name="Custom Depends On", directed=True)]


class TestEvidenceProvider(EvidenceTypeProvider):
    """Contributes a custom evidence type."""

    def get_evidence_types(self) -> list[EvidenceType]:
        return [EvidenceType(id="custom_proof", name="Custom Proof")]


class TitlePrefixValidator(KnowledgeValidator):
    """Custom validator ensuring titles start with an uppercase letter."""

    name = "title_prefix"

    def validate_object(self, obj, catalog=None, framework=None):
        if obj.title and not obj.title[0].isupper():
            return ValidationResult.failure(
                [Diagnostic("error", "bad_title", "Title must start with an uppercase letter")]
            )
        return ValidationResult.success()


class TestValidatorProvider(KnowledgeValidatorProvider):
    """Contributes the custom validator."""

    def get_validators(self):
        return [TitlePrefixValidator]


def register(api):
    """Register all knowledge plugin ports."""
    api.register_port("knowledge_type_provider", TestTypeProvider())
    api.register_port("relationship_type_provider", TestRelationshipProvider())
    api.register_port("evidence_type_provider", TestEvidenceProvider())
    api.register_port("knowledge_validator_provider", TestValidatorProvider())
