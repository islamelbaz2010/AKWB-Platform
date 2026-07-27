"""Tests for extraction segmenters."""

from akwb.extraction.models import ContentKind, NormalizedContent, SegmentType
from akwb.extraction.segmenters import (
    AdaptiveSegmenter,
    CodeSegmenter,
    HeadingSegmenter,
    ParagraphSegmenter,
    SemanticSegmenter,
    StructuralSegmenter,
    TableSegmenter,
)


def _text_content(text: str) -> NormalizedContent:
    return NormalizedContent(
        kind=ContentKind.TEXT,
        mime_type="text/plain",
        content=text,
        source_uri="doc.txt",
    )


def test_heading_segmenter_finds_atx_headings() -> None:
    text = "# Title\n## Section\nparagraph"
    segments = HeadingSegmenter().segment(_text_content(text))
    assert len(segments) == 2
    assert segments[0].type == SegmentType.HEADING
    assert segments[0].content == "Title"
    assert segments[0].label == "h1"
    assert segments[1].label == "h2"


def test_heading_segmenter_finds_setext_headings() -> None:
    text = "Title\n=====\n\nSubtitle\n-------\n"
    segments = HeadingSegmenter().segment(_text_content(text))
    titles = [s.content for s in segments]
    assert "Title" in titles
    assert "Subtitle" in titles


def test_paragraph_segmenter_splits_blocks() -> None:
    text = "First paragraph.\n\nSecond paragraph."
    segments = ParagraphSegmenter().segment(_text_content(text))
    assert len(segments) == 2
    assert segments[0].content == "First paragraph."
    assert segments[1].content == "Second paragraph."


def test_paragraph_segmenter_skips_headings_and_code() -> None:
    text = "# Heading\n\nA paragraph.\n\n```\ncode\n```\n\nAnother."
    segments = ParagraphSegmenter().segment(_text_content(text))
    assert all(s.content not in {"# Heading", "```", "code"} for s in segments)
    assert len(segments) == 2


def test_code_segmenter_finds_fenced_blocks() -> None:
    text = "```python\ndef f():\n    pass\n```"
    segments = CodeSegmenter().segment(_text_content(text))
    assert len(segments) == 1
    assert segments[0].type == SegmentType.CODE
    assert "def f():" in segments[0].content
    assert segments[0].label == "python"


def test_table_segmenter_finds_markdown_table() -> None:
    text = "| A | B |\n|---|---|\n| 1 | 2 |"
    segments = TableSegmenter().segment(_text_content(text))
    assert len(segments) == 1
    assert segments[0].type == SegmentType.TABLE
    assert segments[0].content == [["A", "B"], ["1", "2"]]


def test_structural_segmenter_segments_dict() -> None:
    content = NormalizedContent(
        kind=ContentKind.STRUCTURED,
        mime_type="application/json",
        content={"name": "Alice", "tags": ["x", "y"]},
        source_uri="data.json",
    )
    segments = StructuralSegmenter().segment(content)
    labels = {s.label for s in segments}
    assert "name" in labels
    assert "tags[0]" in labels
    assert "tags[1]" in labels


def test_semantic_segmenter_splits_sentences() -> None:
    text = "First sentence. Second sentence! Third?"
    segments = SemanticSegmenter().segment(_text_content(text))
    assert len(segments) == 3
    assert all(s.type == SegmentType.SEMANTIC for s in segments)
    assert "Second sentence" in segments[1].content


def test_adaptive_segmenter_uses_registered_segmenters() -> None:
    text = "# Heading\n\nA paragraph."
    adaptive = AdaptiveSegmenter(
        [HeadingSegmenter(), ParagraphSegmenter(), CodeSegmenter()]
    )
    segments = adaptive.segment(_text_content(text))
    assert len(segments) == 2
    assert {s.type for s in segments} == {SegmentType.HEADING, SegmentType.PARAGRAPH}
