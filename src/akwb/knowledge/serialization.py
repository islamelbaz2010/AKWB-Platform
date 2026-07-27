"""Serialization support for the Enterprise Knowledge Object Framework.

Formats supported:
- JSON
- JSONL
- YAML

The catalog and individual objects are serialized through Pydantic's JSON/dict
machinery, keeping the serialization layer thin and replaceable.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, ClassVar

import yaml

from akwb.knowledge.models import (
    EvidenceType,
    KnowledgeCatalog,
    KnowledgeObject,
    KnowledgeRelationship,
    KnowledgeType,
    RelationshipType,
)


class SerializationFormat:
    """Namespace for supported serialization formats."""

    JSON = "json"
    JSONL = "jsonl"
    YAML = "yaml"


class KnowledgeSerializer(ABC):
    """Abstract serializer for knowledge objects and catalogs."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical format name."""
        ...

    @abstractmethod
    def serialize_catalog(self, catalog: KnowledgeCatalog) -> str:
        """Serialize a ``KnowledgeCatalog`` to a string."""
        ...

    @abstractmethod
    def deserialize_catalog(self, data: str) -> KnowledgeCatalog:
        """Deserialize a string into a ``KnowledgeCatalog``."""
        ...

    @abstractmethod
    def serialize_object(self, obj: KnowledgeObject) -> str:
        """Serialize a single ``KnowledgeObject`` to a string."""
        ...

    @abstractmethod
    def deserialize_object(self, data: str) -> KnowledgeObject:
        """Deserialize a string into a ``KnowledgeObject``."""
        ...


class JsonSerializer(KnowledgeSerializer):
    """Compact / indented JSON serializer."""

    name: str = "json"

    def serialize_catalog(self, catalog: KnowledgeCatalog) -> str:
        return catalog.model_dump_json(indent=2, by_alias=False)

    def deserialize_catalog(self, data: str) -> KnowledgeCatalog:
        raw = json.loads(data)
        return KnowledgeCatalog.model_validate(raw)

    def serialize_object(self, obj: KnowledgeObject) -> str:
        return obj.model_dump_json(indent=2, by_alias=False)

    def deserialize_object(self, data: str) -> KnowledgeObject:
        raw = json.loads(data)
        return KnowledgeObject.model_validate(raw)


class YamlSerializer(KnowledgeSerializer):
    """YAML serializer using PyYAML."""

    name: str = "yaml"

    def serialize_catalog(self, catalog: KnowledgeCatalog) -> str:
        payload = catalog.model_dump(mode="json", by_alias=False)
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    def deserialize_catalog(self, data: str) -> KnowledgeCatalog:
        raw = yaml.safe_load(data)
        if not isinstance(raw, dict):
            raise TypeError("YAML catalog must contain a top-level mapping")
        return KnowledgeCatalog.model_validate(raw)

    def serialize_object(self, obj: KnowledgeObject) -> str:
        payload = obj.model_dump(mode="json", by_alias=False)
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    def deserialize_object(self, data: str) -> KnowledgeObject:
        raw = yaml.safe_load(data)
        if not isinstance(raw, dict):
            raise TypeError("YAML object must contain a top-level mapping")
        return KnowledgeObject.model_validate(raw)


class JsonlSerializer(KnowledgeSerializer):
    """Line-delimited JSON serializer.

    Each line contains a record with ``kind`` and ``data`` keys.  The catalog is
    reconstructed by grouping records by kind and indexing them by ``id``.
    """

    name: str = "jsonl"

    _MODELS: ClassVar[dict[str, Any]] = {
        "KnowledgeType": KnowledgeType,
        "RelationshipType": RelationshipType,
        "EvidenceType": EvidenceType,
        "KnowledgeObject": KnowledgeObject,
        "KnowledgeRelationship": KnowledgeRelationship,
    }

    def serialize_catalog(self, catalog: KnowledgeCatalog) -> str:
        lines: list[str] = []
        for kind, collection in (
            ("KnowledgeType", catalog.types.values()),
            ("RelationshipType", catalog.relationship_types.values()),
            ("EvidenceType", catalog.evidence_types.values()),
            ("KnowledgeObject", catalog.objects.values()),
            ("KnowledgeRelationship", catalog.relationships.values()),
        ):
            for item in collection:
                record = {
                    "kind": kind,
                    "data": item.model_dump(mode="json", by_alias=False),
                }
                lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        if catalog.metadata:
            lines.append(
                json.dumps(
                    {"kind": "metadata", "data": catalog.metadata},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        return "\n".join(lines) + ("\n" if lines else "")

    def deserialize_catalog(self, data: str) -> KnowledgeCatalog:
        if not data.strip():
            return KnowledgeCatalog()

        types_map: dict[str, KnowledgeType] = {}
        rel_types_map: dict[str, RelationshipType] = {}
        evidence_types_map: dict[str, EvidenceType] = {}
        objects_map: dict[str, KnowledgeObject] = {}
        relationships_map: dict[str, KnowledgeRelationship] = {}
        metadata: dict[str, Any] = {}

        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            kind = record.get("kind")
            payload = record.get("data", {})
            if kind == "metadata":
                metadata.update(payload)
                continue
            model_cls = self._MODELS.get(kind)
            if model_cls is None:
                raise ValueError(f"Unknown catalog record kind: {kind!r}")
            item = model_cls.model_validate(payload)
            if kind == "KnowledgeType":
                types_map[item.id] = item
            elif kind == "RelationshipType":
                rel_types_map[item.id] = item
            elif kind == "EvidenceType":
                evidence_types_map[item.id] = item
            elif kind == "KnowledgeObject":
                objects_map[item.id] = item
            elif kind == "KnowledgeRelationship":
                relationships_map[item.id] = item

        return KnowledgeCatalog(
            metadata=metadata,
            types=types_map,
            relationship_types=rel_types_map,
            evidence_types=evidence_types_map,
            objects=objects_map,
            relationships=relationships_map,
        )

    def serialize_object(self, obj: KnowledgeObject) -> str:
        return json.dumps(
            {"kind": "KnowledgeObject", "data": obj.model_dump(mode="json", by_alias=False)},
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def deserialize_object(self, data: str) -> KnowledgeObject:
        record = json.loads(data)
        return KnowledgeObject.model_validate(record["data"])
