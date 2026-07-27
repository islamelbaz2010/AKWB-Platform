"""Validation framework for the Enterprise Knowledge Object Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from akwb.types import Diagnostic

if TYPE_CHECKING:
    from akwb.knowledge.framework import KnowledgeFramework
    from akwb.knowledge.models import KnowledgeCatalog, KnowledgeObject, KnowledgeRelationship


@dataclass
class ValidationResult:
    """Result of validating a knowledge object, relationship, or catalog."""

    ok: bool = True
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another validation result into this one in place."""
        self.ok = self.ok and other.ok
        self.diagnostics.extend(other.diagnostics)
        return self

    @staticmethod
    def success(diagnostics: list[Diagnostic] | None = None) -> ValidationResult:
        return ValidationResult(ok=True, diagnostics=diagnostics or [])

    @staticmethod
    def failure(diagnostics: list[Diagnostic]) -> ValidationResult:
        return ValidationResult(ok=False, diagnostics=diagnostics)


class KnowledgeValidator(ABC):
    """Base class for all knowledge validators."""

    name: str = ""

    @abstractmethod
    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        """Validate a knowledge object."""
        ...

    def validate_relationship(
        self,
        relationship: KnowledgeRelationship,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        """Validate a relationship.

        Most validators do not care about relationships; the default is success.
        """
        return ValidationResult.success()


class CompositeValidator(KnowledgeValidator):
    """Run a collection of validators and merge their results."""

    name = "composite"

    def __init__(self, validators: list[KnowledgeValidator]) -> None:
        self.validators = validators

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        result = ValidationResult.success()
        for validator in self.validators:
            result.merge(validator.validate_object(obj, catalog, framework))
        return result

    def validate_relationship(
        self,
        relationship: KnowledgeRelationship,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        result = ValidationResult.success()
        for validator in self.validators:
            result.merge(validator.validate_relationship(relationship, catalog, framework))
        return result


class TypeValidator(KnowledgeValidator):
    """Validate that a knowledge object's type is registered and content matches its schema."""

    name = "type"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        if framework is None or not framework.type_registry.has(obj.type):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "unknown_knowledge_type",
                    f"Knowledge type {obj.type!r} is not registered",
                    source_ref=obj.id,
                )
            )
            return ValidationResult.failure(diagnostics)

        type_def = framework.type_registry.get(obj.type)
        if type_def and type_def.content_schema:
            if obj.content is None:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "missing_content",
                        f"Knowledge type {obj.type!r} requires content but none was provided",
                        source_ref=obj.id,
                    )
                )
            elif isinstance(obj.content, dict):
                diagnostics.extend(self._validate_schema(obj, type_def.content_schema))
            else:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invalid_content_shape",
                        f"Content must be a mapping for type {obj.type!r}",
                        source_ref=obj.id,
                    )
                )

        if diagnostics:
            return ValidationResult.failure(diagnostics)
        return ValidationResult.success()

    def _validate_schema(
        self, obj: KnowledgeObject, schema: dict[str, Any]
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        if not isinstance(obj.content, dict):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_content_shape",
                    f"Content must be a mapping for type {obj.type!r}",
                    source_ref=obj.id,
                )
            )
            return diagnostics

        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in obj.content:
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "missing_required_field",
                            f"Required field {key!r} missing for type {obj.type!r}",
                            source_ref=obj.id,
                        )
                    )

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, prop in properties.items():
                if key not in obj.content:
                    continue
                expected_type = prop.get("type") if isinstance(prop, dict) else None
                if expected_type:
                    diagnostics.extend(
                        self._check_json_type(obj, key, obj.content[key], expected_type)
                    )

        return diagnostics

    def _check_json_type(
        self, obj: KnowledgeObject, key: str, value: Any, expected: str
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        type_map = {
            "string": (str,),
            "number": (int, float),
            "integer": (int,),
            "boolean": (bool,),
            "array": (list,),
            "object": (dict,),
            "null": (type(None),),
        }
        allowed = type_map.get(expected)
        if allowed and not isinstance(value, allowed):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "field_type_mismatch",
                    f"Field {key!r} expected {expected!r} but got {type(value).__name__}",
                    source_ref=obj.id,
                )
            )
        return diagnostics


class RelationshipValidator(KnowledgeValidator):
    """Validate relationship types, endpoints, and type constraints."""

    name = "relationship"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        """Relationships are not validated at the object level."""
        return ValidationResult.success()

    def validate_relationship(
        self,
        relationship: KnowledgeRelationship,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []

        if framework is None or not framework.relationship_type_registry.has(relationship.relationship_type):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "unknown_relationship_type",
                    f"Relationship type {relationship.relationship_type!r} is not registered",
                    source_ref=relationship.id,
                )
            )
            return ValidationResult.failure(diagnostics)

        rel_type = framework.relationship_type_registry.get(relationship.relationship_type)

        if catalog is not None:
            for ref, role in ((relationship.from_ref, "from"), (relationship.to_ref, "to")):
                if ref.kind.value == "knowledge_object" and not catalog.get_object(ref.ref):
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "missing_relationship_endpoint",
                            f"{role}_ref {ref.ref!r} does not exist in the catalog",
                            source_ref=relationship.id,
                        )
                    )

            if rel_type:
                diagnostics.extend(self._check_type_constraints(relationship, rel_type, catalog))

        if diagnostics:
            return ValidationResult.failure(diagnostics)
        return ValidationResult.success()

    def _check_type_constraints(
        self,
        relationship: KnowledgeRelationship,
        rel_type: Any,
        catalog: KnowledgeCatalog,
    ) -> list[Diagnostic]:
        diagnostics: list[Diagnostic] = []
        from_obj = catalog.get_object(relationship.from_ref.ref)
        to_obj = catalog.get_object(relationship.to_ref.ref)

        allowed_from = getattr(rel_type, "allowed_from_types", None)
        if allowed_from and from_obj and from_obj.type not in allowed_from:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_from_type",
                    f"Type {from_obj.type!r} not allowed as source for {rel_type.id!r}",
                    source_ref=relationship.id,
                )
            )

        allowed_to = getattr(rel_type, "allowed_to_types", None)
        if allowed_to and to_obj and to_obj.type not in allowed_to:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_to_type",
                    f"Type {to_obj.type!r} not allowed as target for {rel_type.id!r}",
                    source_ref=relationship.id,
                )
            )

        return diagnostics


class EvidenceValidator(KnowledgeValidator):
    """Validate evidence entries attached to a knowledge object."""

    name = "evidence"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        for evidence in obj.evidence:
            if not evidence.source.uri:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "missing_evidence_source_uri",
                        "Evidence source must provide a URI",
                        source_ref=obj.id,
                    )
                )
            if not evidence.source.kind:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "missing_evidence_source_kind",
                        "Evidence source must declare a kind",
                        source_ref=obj.id,
                    )
                )
            if framework and not framework.evidence_type_registry.has(evidence.type):
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "unknown_evidence_type",
                        f"Evidence type {evidence.type!r} is not registered",
                        source_ref=obj.id,
                    )
                )
            if evidence.confidence.value < 0.0 or evidence.confidence.value > 1.0:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invalid_confidence",
                        f"Confidence must be in [0.0, 1.0], got {evidence.confidence.value}",
                        source_ref=obj.id,
                    )
                )

        if diagnostics:
            return ValidationResult.failure(diagnostics)
        return ValidationResult.success()


class TraceabilityValidator(KnowledgeValidator):
    """Ensure every knowledge object is traceable to at least one source or evidence."""

    name = "traceability"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        if not obj.sources and not obj.evidence:
            return ValidationResult.failure(
                [
                    Diagnostic(
                        "error",
                        "missing_traceability",
                        "Knowledge object has no sources or evidence",
                        source_ref=obj.id,
                    )
                ]
            )
        return ValidationResult.success()


class MetadataValidator(KnowledgeValidator):
    """Validate metadata fields and tags."""

    name = "metadata"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        if not obj.metadata.schema_version:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing_schema_version",
                    "metadata.schema_version is required",
                    source_ref=obj.id,
                )
            )
        if not obj.metadata.created_at:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing_created_at",
                    "metadata.created_at is required",
                    source_ref=obj.id,
                )
            )
        for tag in obj.metadata.tags:
            if not isinstance(tag, str):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invalid_tag",
                        f"Tags must be strings, got {type(tag).__name__}",
                        source_ref=obj.id,
                    )
                )
        if diagnostics:
            return ValidationResult.failure(diagnostics)
        return ValidationResult.success()


class ConfidenceValidator(KnowledgeValidator):
    """Validate object-level confidence values."""

    name = "confidence"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        if obj.confidence.value < 0.0 or obj.confidence.value > 1.0:
            return ValidationResult.failure(
                [
                    Diagnostic(
                        "error",
                        "invalid_confidence",
                        f"Confidence must be in [0.0, 1.0], got {obj.confidence.value}",
                        source_ref=obj.id,
                    )
                ]
            )
        return ValidationResult.success()


class LifecycleValidator(KnowledgeValidator):
    """Validate lifecycle/version consistency."""

    name = "lifecycle"

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        diagnostics: list[Diagnostic] = []
        if obj.lifecycle.state != obj.version.state:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "lifecycle_version_mismatch",
                    f"lifecycle.state ({obj.lifecycle.state.value}) != version.state ({obj.version.state.value})",
                    source_ref=obj.id,
                )
            )

        if obj.version.state.value == "superseded" and not obj.version.superseded_by_id:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "missing_superseded_by",
                    "Superseded version must specify superseded_by_id",
                    source_ref=obj.id,
                )
            )

        if obj.version.state.value == "archived" and not obj.version.archived_at:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "missing_archived_at",
                    "Archived version is missing archived_at",
                    source_ref=obj.id,
                )
            )

        if (
            obj.version.previous_version_id
            and catalog is not None
            and not catalog.get_object(obj.version.previous_version_id)
        ):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "missing_previous_version",
                    f"Previous version {obj.version.previous_version_id!r} not in catalog",
                    source_ref=obj.id,
                )
            )

        if diagnostics:
            return ValidationResult(ok=all(d.level != "error" for d in diagnostics), diagnostics=diagnostics)
        return ValidationResult.success()


class ValidatorRegistry:
    """Registry of ``KnowledgeValidator`` instances."""

    def __init__(self) -> None:
        self._validators: list[KnowledgeValidator] = []

    def register(self, validator: KnowledgeValidator | type[KnowledgeValidator]) -> None:
        """Register a validator instance or class."""
        if isinstance(validator, type):
            validator = validator()
        if not isinstance(validator, KnowledgeValidator):
            raise TypeError(f"Expected KnowledgeValidator, got {type(validator).__name__}")
        self._validators.append(validator)

    def validate_object(
        self,
        obj: KnowledgeObject,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        result = ValidationResult.success()
        for validator in self._validators:
            result.merge(validator.validate_object(obj, catalog, framework))
        return result

    def validate_relationship(
        self,
        relationship: KnowledgeRelationship,
        catalog: KnowledgeCatalog | None = None,
        framework: KnowledgeFramework | None = None,
    ) -> ValidationResult:
        result = ValidationResult.success()
        for validator in self._validators:
            result.merge(validator.validate_relationship(relationship, catalog, framework))
        return result
