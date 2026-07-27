"""Tests for generic knowledge type registries."""

from __future__ import annotations

import pytest

from akwb.knowledge.builtins import BUILTIN_TYPES
from akwb.knowledge.models import KnowledgeType
from akwb.knowledge.registries import TypeRegistry


def test_type_registry_register_and_get() -> None:
    registry = TypeRegistry[KnowledgeType]()
    kt = KnowledgeType(id="custom", name="Custom")
    registry.register(kt)
    assert registry.has("custom")
    assert registry.get("custom") is kt


def test_type_registry_register_all() -> None:
    registry = TypeRegistry[KnowledgeType]()
    registry.register_all(BUILTIN_TYPES)
    assert len(registry) == len(BUILTIN_TYPES)
    assert registry.has("decision")


def test_type_registry_missing_id() -> None:
    registry = TypeRegistry[KnowledgeType]()
    with pytest.raises(ValueError):
        registry.register(KnowledgeType(id="", name="Bad"))


def test_type_registry_iteration() -> None:
    registry = TypeRegistry[KnowledgeType]()
    registry.register(KnowledgeType(id="a", name="A"))
    registry.register(KnowledgeType(id="b", name="B"))
    ids = {k for k, _ in registry}
    assert ids == {"a", "b"}


def test_type_registry_contains() -> None:
    registry = TypeRegistry[KnowledgeType]()
    registry.register(KnowledgeType(id="x", name="X"))
    assert "x" in registry
    assert "y" not in registry
