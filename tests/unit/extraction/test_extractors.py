"""Tests for the rule-based extractor."""

from akwb.extraction.extractors import RuleBasedExtractor
from akwb.extraction.models import Segment, SegmentType
from akwb.knowledge.models import KnowledgeSource


def _source() -> KnowledgeSource:
    return KnowledgeSource(kind="markdown", uri="doc.md")


def test_extract_heading() -> None:
    segment = Segment(type=SegmentType.HEADING, content="Decision to use Postgres")
    extractor = RuleBasedExtractor()
    candidates = extractor.extract([segment], _source())
    assert len(candidates) == 1
    assert candidates[0].knowledge_type == "decision"
    assert candidates[0].title == "Decision to use Postgres"


def test_extract_paragraph_with_keywords() -> None:
    segment = Segment(type=SegmentType.PARAGRAPH, content="The system must support 1000 users.")
    extractor = RuleBasedExtractor()
    candidates = extractor.extract([segment], _source())
    assert candidates[0].knowledge_type == "requirement"
    assert candidates[0].title == "The system must support 1000 users."


def test_extract_code() -> None:
    segment = Segment(type=SegmentType.CODE, label="python", content="def main(): pass")
    extractor = RuleBasedExtractor()
    candidates = extractor.extract([segment], _source())
    assert candidates[0].knowledge_type == "component"
    assert candidates[0].title == "Code snippet"


def test_extract_table() -> None:
    segment = Segment(
        type=SegmentType.TABLE,
        content=[["Option", "Decision"], ["DB", "Postgres"]],
        location="lines 10-12",
    )
    extractor = RuleBasedExtractor()
    candidates = extractor.extract([segment], _source())
    assert candidates[0].knowledge_type == "business_rule"
    assert "Table" in candidates[0].title


def test_extract_structural() -> None:
    segment = Segment(
        type=SegmentType.STRUCTURAL, label="decision", content="Use Postgres"
    )
    extractor = RuleBasedExtractor()
    candidates = extractor.extract([segment], _source())
    assert candidates[0].knowledge_type == "decision"
    assert candidates[0].title == "decision"
