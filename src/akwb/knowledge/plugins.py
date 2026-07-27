"""Plugin extension ports for the Enterprise Knowledge Object Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod

from akwb.domain.ports import PluginPort
from akwb.knowledge.models import (
    EvidenceType,
    KnowledgeType,
    RelationshipType,
)
from akwb.knowledge.validation import KnowledgeValidator


class KnowledgeTypeProvider(PluginPort, ABC):
    """Contribute built-in or domain-specific knowledge types."""

    port_name: str = "knowledge_type_provider"

    @abstractmethod
    def get_types(self) -> list[KnowledgeType]:
        """Return the knowledge types contributed by this plugin."""
        ...


class RelationshipTypeProvider(PluginPort, ABC):
    """Contribute built-in or domain-specific relationship types."""

    port_name: str = "relationship_type_provider"

    @abstractmethod
    def get_relationship_types(self) -> list[RelationshipType]:
        """Return the relationship types contributed by this plugin."""
        ...


class EvidenceTypeProvider(PluginPort, ABC):
    """Contribute evidence type definitions."""

    port_name: str = "evidence_type_provider"

    @abstractmethod
    def get_evidence_types(self) -> list[EvidenceType]:
        """Return the evidence types contributed by this plugin."""
        ...


class KnowledgeValidatorProvider(PluginPort, ABC):
    """Contribute custom knowledge validators."""

    port_name: str = "knowledge_validator_provider"

    @abstractmethod
    def get_validators(self) -> list[KnowledgeValidator | type[KnowledgeValidator]]:
        """Return validator instances or classes contributed by this plugin."""
        ...
