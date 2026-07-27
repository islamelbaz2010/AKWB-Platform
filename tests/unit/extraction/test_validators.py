"""Tests for candidate validators."""

from akwb.extraction.builders import (
    RegisteredTypeCandidateValidator,
    RequiredFieldsCandidateValidator,
)
from akwb.extraction.models import ExtractionCandidate
from akwb.extraction.pipeline import ExtractionContext
from akwb.knowledge.framework import KnowledgeFramework
from akwb.knowledge.models import KnowledgeSource


def _source() -> KnowledgeSource:
    return KnowledgeSource(kind="markdown", uri="doc.md")


def test_required_fields_validator_rejects_missing_title() -> None:
    candidate = ExtractionCandidate(
        knowledge_type="decision", title="", source=_source()
    )
    result = RequiredFieldsCandidateValidator().validate(candidate)
    assert not result.ok
    assert any("missing_title" in d.code for d in result.diagnostics)


def test_required_fields_validator_accepts_valid() -> None:
    candidate = ExtractionCandidate(
        knowledge_type="decision", title="Use Postgres", source=_source()
    )
    result = RequiredFieldsCandidateValidator().validate(candidate)
    assert result.ok


def test_registered_type_validator_checks_framework() -> None:
    framework = KnowledgeFramework()
    context = ExtractionContext(framework=framework)
    good = ExtractionCandidate(
        knowledge_type="decision", title="Use Postgres", source=_source()
    )
    bad = ExtractionCandidate(
        knowledge_type="not_a_type", title="Bad", source=_source()
    )
    validator = RegisteredTypeCandidateValidator()

    assert validator.validate(good, context).ok
    result = validator.validate(bad, context)
    assert not result.ok
    assert any("unknown_knowledge_type" in d.code for d in result.diagnostics)
