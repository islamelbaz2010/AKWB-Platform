"""Central orchestrator for the Enterprise Knowledge Object Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from akwb.domain.ports import Observability, PluginPort
from akwb.knowledge.builtins import (
    BUILTIN_EVIDENCE_TYPES,
    BUILTIN_RELATIONSHIP_TYPES,
    BUILTIN_TYPES,
)
from akwb.knowledge.models import (
    EvidenceType,
    KnowledgeCatalog,
    KnowledgeRelationship,
    KnowledgeType,
    RelationshipType,
)
from akwb.knowledge.plugins import (
    KnowledgeValidatorProvider,
)
from akwb.knowledge.registries import TypeRegistry
from akwb.knowledge.serialization import (
    JsonlSerializer,
    JsonSerializer,
    KnowledgeSerializer,
    YamlSerializer,
)
from akwb.knowledge.validation import (
    ConfidenceValidator,
    EvidenceValidator,
    LifecycleValidator,
    MetadataValidator,
    RelationshipValidator,
    TraceabilityValidator,
    TypeValidator,
    ValidationResult,
    ValidatorRegistry,
)

if TYPE_CHECKING:
    from akwb.knowledge.models import KnowledgeObject
    from akwb.plugins.registry import PluginRegistry


class KnowledgeFramework:
    """Orchestrates knowledge types, validators, and serialization.

    The framework loads built-in defaults, optionally extends them from the
    plugin registry, and exposes validation and factory methods for building
    ``KnowledgeCatalog`` instances.
    """

    def __init__(self, observability: Observability | None = None) -> None:
        self.observability = observability
        self.type_registry: TypeRegistry[KnowledgeType] = TypeRegistry[KnowledgeType]()
        self.relationship_type_registry: TypeRegistry[RelationshipType] = TypeRegistry[RelationshipType]()
        self.evidence_type_registry: TypeRegistry[EvidenceType] = TypeRegistry[EvidenceType]()
        self.validator_registry = ValidatorRegistry()

        # Register built-in serializers keyed by their canonical format.
        self.serializers: dict[str, KnowledgeSerializer] = {
            "json": JsonSerializer(),
            "jsonl": JsonlSerializer(),
            "yaml": YamlSerializer(),
        }

        self._load_builtins()

    def _load_builtins(self) -> None:
        """Load built-in types, relationship types, evidence types, and validators."""
        for kt in BUILTIN_TYPES:
            self.type_registry.register(kt)
        for rt in BUILTIN_RELATIONSHIP_TYPES:
            self.relationship_type_registry.register(rt)
        for et in BUILTIN_EVIDENCE_TYPES:
            self.evidence_type_registry.register(et)

        self.validator_registry.register(TypeValidator())
        self.validator_registry.register(RelationshipValidator())
        self.validator_registry.register(EvidenceValidator())
        self.validator_registry.register(TraceabilityValidator())
        self.validator_registry.register(MetadataValidator())
        self.validator_registry.register(ConfidenceValidator())
        self.validator_registry.register(LifecycleValidator())

    def load_plugins(self, plugin_registry: PluginRegistry) -> None:
        """Extend the framework from a populated ``PluginRegistry``."""
        self._register_from_providers(
            plugin_registry.resolve("knowledge_type_provider"),
            self.type_registry,
            "get_types",
        )
        self._register_from_providers(
            plugin_registry.resolve("relationship_type_provider"),
            self.relationship_type_registry,
            "get_relationship_types",
        )
        self._register_from_providers(
            plugin_registry.resolve("evidence_type_provider"),
            self.evidence_type_registry,
            "get_evidence_types",
        )

        for provider in plugin_registry.resolve("knowledge_validator_provider"):
            instance = self._instantiate_provider(provider)
            if isinstance(instance, KnowledgeValidatorProvider):
                for validator in instance.get_validators():
                    self.validator_registry.register(validator)

    def _register_from_providers(
        self,
        providers: list[PluginPort],
        registry: TypeRegistry[Any],
        method_name: str,
    ) -> None:
        """Resolve provider instances and register their contributions."""
        for provider in providers:
            instance = self._instantiate_provider(provider)
            getter = getattr(instance, method_name, None)
            if getter is None:
                if self.observability:
                    self.observability.warning(
                        f"Knowledge provider {type(instance).__name__} missing {method_name}"
                    )
                continue
            for item in getter():
                registry.register(item)

    @staticmethod
    def _instantiate_provider(provider: PluginPort) -> PluginPort:
        """Return a provider instance, instantiating the class if necessary."""
        if isinstance(provider, type):
            return cast(PluginPort, provider())
        return provider

    def _typed_serializer(self, name: str) -> KnowledgeSerializer:
        """Return the serializer for ``name`` as a KnowledgeSerializer."""
        serializer = self.serializers.get(name)
        if serializer is None:
            raise ValueError(f"Unknown serialization format: {name!r}")
        return serializer

    # --- Convenience accessors ------------------------------------------------

    def get_type(self, type_id: str) -> object | None:
        return self.type_registry.get(type_id)

    def get_relationship_type(self, relationship_type_id: str) -> object | None:
        return self.relationship_type_registry.get(relationship_type_id)

    def get_evidence_type(self, evidence_type_id: str) -> object | None:
        return self.evidence_type_registry.get(evidence_type_id)

    # --- Validation ------------------------------------------------------------

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
    ) -> ValidationResult:
        """Validate a single knowledge object."""
        return self.validator_registry.validate_object(obj, catalog, self)

    def validate_relationship(
        self,
        relationship: KnowledgeRelationship,
        catalog: KnowledgeCatalog | None = None,
    ) -> ValidationResult:
        """Validate a single relationship."""
        return self.validator_registry.validate_relationship(relationship, catalog, self)

    def validate_catalog(self, catalog: KnowledgeCatalog) -> ValidationResult:
        """Validate every object and relationship in the catalog."""
        result = ValidationResult.success()
        for obj in catalog.objects.values():
            result.merge(self.validate_object(obj, catalog))
        for relationship in catalog.relationships.values():
            result.merge(self.validate_relationship(relationship, catalog))
        return result

    # --- Catalog factory -------------------------------------------------------

    def new_catalog(self, **metadata: object) -> KnowledgeCatalog:
        """Return a fresh ``KnowledgeCatalog`` preloaded with framework type definitions."""
        return KnowledgeCatalog(
            metadata=dict(metadata),
            types=self.type_registry.items(),
            relationship_types=self.relationship_type_registry.items(),
            evidence_types=self.evidence_type_registry.items(),
        )

    # --- Serialization helpers -------------------------------------------------

    def get_serializer(self, name: str) -> KnowledgeSerializer:
        """Return the serializer registered for ``name`` (json, jsonl, yaml)."""
        return self._typed_serializer(name)

    def serialize_catalog(self, catalog: KnowledgeCatalog, fmt: str = "json") -> str:
        """Serialize a catalog using the named format."""
        return self._typed_serializer(fmt).serialize_catalog(catalog)

    def deserialize_catalog(self, data: str, fmt: str = "json") -> KnowledgeCatalog:
        """Deserialize a catalog using the named format."""
        return self._typed_serializer(fmt).deserialize_catalog(data)

    def serialize_object(self, obj: KnowledgeObject, fmt: str = "json") -> str:
        """Serialize a single knowledge object using the named format."""
        return self._typed_serializer(fmt).serialize_object(obj)

    def deserialize_object(self, data: str, fmt: str = "json") -> KnowledgeObject:
        """Deserialize a single knowledge object using the named format."""
        return self._typed_serializer(fmt).deserialize_object(data)
