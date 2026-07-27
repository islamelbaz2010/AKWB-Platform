"""Tests for extraction pipeline domain models."""

from akwb.extraction.models import (
    ContentKind,
    ExtractionCandidate,
    NormalizedContent,
    Segment,
    SegmentType,
)
from akwb.knowledge.models import KnowledgeSource


def test_normalized_content_creation() -> None:
    content = NormalizedContent(
        kind=ContentKind.TEXT,
        mime_type="text/plain",
        content="Hello world",
        source_uri="doc.txt",
    )
    assert content.kind == ContentKind.TEXT
    assert content.source_uri == "doc.txt"


def test_segment_creation() -> None:
    segment = Segment(
        type=SegmentType.PARAGRAPH,
        content="A paragraph.",
        location="line 1",
    )
    assert segment.type == SegmentType.PARAGRAPH
    assert segment.content == "A paragraph."


def test_extraction_candidate_creation() -> None:
    source = KnowledgeSource(kind="markdown", uri="doc.md")
    candidate = ExtractionCandidate(
        knowledge_type="decision",
        title="Use Postgres",
        content={"status": "open"},
        source=source,
    )
    assert candidate.knowledge_type == "decision"
    assert candidate.confidence == 1.0
