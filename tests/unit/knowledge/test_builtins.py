"""Tests for built-in knowledge, relationship, and evidence type defaults."""

from __future__ import annotations

from akwb.knowledge.builtins import (
    BUILTIN_EVIDENCE_TYPES,
    BUILTIN_RELATIONSHIP_TYPES,
    BUILTIN_SOURCE_KINDS,
    BUILTIN_TYPES,
)


def test_builtin_knowledge_types_cover_required() -> None:
    ids = {t.id for t in BUILTIN_TYPES}
    required = {
        "decision",
        "requirement",
        "risk",
        "issue",
        "task",
        "timeline_event",
        "business_rule",
        "policy",
        "architecture_element",
        "technology",
        "component",
        "capability",
        "process",
        "goal",
        "objective",
        "stakeholder",
        "entity",
        "glossary_term",
        "question",
        "answer",
        "prompt",
        "meeting",
        "conversation",
        "research_finding",
        "metric",
        "constraint",
        "assumption",
        "dependency",
        "action_item",
        "document",
        "media",
    }
    assert required.issubset(ids), ids


def test_builtin_relationship_types_cover_examples() -> None:
    ids = {r.id for r in BUILTIN_RELATIONSHIP_TYPES}
    required = {
        "depends_on",
        "implements",
        "supersedes",
        "derived_from",
        "references",
        "contains",
        "belongs_to",
        "mitigates",
        "supports",
        "generated_from",
        "related_to",
    }
    assert required.issubset(ids), ids


def test_builtin_evidence_types_exist() -> None:
    ids = {e.id for e in BUILTIN_EVIDENCE_TYPES}
    assert "citation" in ids
    assert "ai_extraction" in ids
    assert "manual" in ids


def test_source_kinds_are_nonempty() -> None:
    assert "markdown" in BUILTIN_SOURCE_KINDS
    assert "chatgpt" in BUILTIN_SOURCE_KINDS
    assert "claude" in BUILTIN_SOURCE_KINDS
    assert "gemini" in BUILTIN_SOURCE_KINDS
    assert all(isinstance(k, str) for k in BUILTIN_SOURCE_KINDS)
