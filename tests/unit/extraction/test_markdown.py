"""Tests for the Enterprise Markdown AST parser."""

from akwb.domain.models import Artifact
from akwb.extraction.markdown import (
    MarkdownASTMapper,
    MarkdownASTVisitor,
    MarkdownASTWalker,
    MarkdownDocument,
    MarkdownNode,
    MarkdownParser,
    MarkdownReader,
    MarkdownSegmenter,
)
from akwb.extraction.models import ContentKind, NormalizedContent, SegmentType
from akwb.extraction.pipeline import ExtractionPipeline


def _sample_markdown() -> str:
    return """---
title: Sample
tags: [a, b]
---
# Title

Paragraph with **bold** and [link](https://example.com).

- item 1
- [x] done
- [ ] not done

> a quote

```python
def f():
    pass
```

| A | B |
|---|---|
| 1 | 2 |

![img](img.png)

<div>html</div>

Footnote reference[^1].

[^1]: footnote text.
"""


def test_parser_returns_document() -> None:
    parser = MarkdownParser()
    doc = parser.parse(_sample_markdown(), source_uri="doc.md")
    assert isinstance(doc, MarkdownDocument)
    assert doc.source_uri == "doc.md"
    assert doc.metadata.get("title") == "Sample"


def test_heading_node() -> None:
    doc = MarkdownParser().parse("# Hello\n\n## World")
    headings = [n for n in doc.children if n.type == "heading"]
    assert len(headings) == 2
    assert headings[0].content == "Hello"
    assert headings[0].level == 1
    assert headings[1].level == 2
    assert headings[0].location == {"start_line": 1, "end_line": 1}


def test_paragraph_with_link_and_bold() -> None:
    doc = MarkdownParser().parse("Para **bold** and [link](https://example.com).")
    para = doc.children[0]
    assert para.type == "paragraph"
    assert para.content == "Para bold and link."
    assert any(c.type == "link" for c in para.children)


def test_list_and_task_list() -> None:
    doc = MarkdownParser().parse("- plain\n- [x] done\n- [ ] not")
    lists = [n for n in doc.children if n.type == "list"]
    assert len(lists) == 1
    assert len(lists[0].content) == 3


def test_nested_list() -> None:
    text = """- parent
  - child one
  - child two
"""
    doc = MarkdownParser().parse(text)
    root_list = next(n for n in doc.children if n.type == "list")
    assert len(root_list.children) == 1
    nested = [c for c in root_list.children[0].children if c.type == "list"]
    assert len(nested) == 1
    assert len(nested[0].children) == 2


def test_quote_node() -> None:
    doc = MarkdownParser().parse("> a quote")
    quote = doc.children[0]
    assert quote.type == "quote"
    assert quote.content == "a quote"


def test_code_block() -> None:
    doc = MarkdownParser().parse("```python\ncode\n```")
    code = doc.children[0]
    assert code.type == "code"
    assert code.content == "code\n"
    assert code.metadata.get("language") == "python"


def test_table_node() -> None:
    doc = MarkdownParser().parse("| A | B |\n|---|---|\n| 1 | 2 |")
    table = doc.children[0]
    assert table.type == "table"
    assert table.content == [["A", "B"], ["1", "2"]]


def test_html_block() -> None:
    doc = MarkdownParser().parse("<div>content</div>")
    html = doc.children[0]
    assert html.type == "html"
    assert "<div>" in html.content


def test_image_node() -> None:
    doc = MarkdownParser().parse("![alt](src.png)")
    para = doc.children[0]
    images = [c for c in para.children if c.type == "image"]
    assert len(images) == 1
    assert images[0].content == "alt"
    assert images[0].attrs.get("src") == "src.png"


def _find_nodes(node: MarkdownNode, node_type: str) -> list[MarkdownNode]:
    found: list[MarkdownNode] = []
    if node.type == node_type:
        found.append(node)
    for child in node.children:
        found.extend(_find_nodes(child, node_type))
    return found


def test_footnote_node() -> None:
    doc = MarkdownParser().parse("text[^1].\n\n[^1]: note.")
    footnotes = _find_nodes(doc, "footnote")
    assert len(footnotes) == 1
    assert footnotes[0].content == "note."
    assert footnotes[0].metadata.get("label") == "1"


def test_source_locations() -> None:
    doc = MarkdownParser().parse("# H1\n\nParagraph line 3.")
    heading = doc.children[0]
    para = doc.children[1]
    assert heading.location["start_line"] == 1
    assert para.location["start_line"] == 3


def test_ast_walker_visits_all_nodes() -> None:
    doc = MarkdownParser().parse(_sample_markdown())

    class CountingVisitor(MarkdownASTVisitor):
        def __init__(self) -> None:
            self.counts: dict[str, int] = {}

        def visit_default(self, node: MarkdownNode) -> None:
            self.counts[node.type] = self.counts.get(node.type, 0) + 1

    visitor = CountingVisitor()
    MarkdownASTWalker().walk(doc, visitor)
    assert visitor.counts.get("heading", 0) == 1
    assert visitor.counts.get("paragraph", 0) >= 1
    assert visitor.counts.get("list", 0) >= 1
    assert visitor.counts.get("code", 0) == 1
    assert visitor.counts.get("table", 0) == 1


def test_mapper_returns_normalized_content() -> None:
    artifact = Artifact(name="x.md", relative_path="x.md", mime_type="text/markdown")
    mapper = MarkdownASTMapper()
    normalized = mapper.map("# T\n\np", artifact)
    assert normalized.kind == ContentKind.MARKDOWN
    assert normalized.mime_type == "text/markdown"
    assert isinstance(normalized.content, MarkdownDocument)


def test_reader_produces_markdown_content() -> None:
    artifact = Artifact(name="x.md", relative_path="x.md", mime_type="text/markdown")
    reader = MarkdownReader()
    normalized = reader.read(artifact, b"# T\n\np")
    assert normalized.kind == ContentKind.MARKDOWN
    assert normalized.content.children[0].type == "heading"


def test_segmenter_produces_rich_segments() -> None:
    doc = MarkdownParser().parse(_sample_markdown())
    segmenter = MarkdownSegmenter()
    normalized = NormalizedContent(
        kind=ContentKind.MARKDOWN,
        mime_type="text/markdown",
        content=doc,
        source_uri="doc.md",
    )
    segments = segmenter.segment(normalized)
    types = {s.type for s in segments}
    assert SegmentType.HEADING in types
    assert SegmentType.PARAGRAPH in types
    assert SegmentType.CODE in types
    assert SegmentType.TABLE in types
    assert SegmentType.QUOTE in types
    assert SegmentType.TASK_LIST in types
    assert SegmentType.HTML in types
    assert SegmentType.METADATA in types
    assert SegmentType.FOOTNOTE in types


def test_paragraph_image_becomes_image_segment() -> None:
    doc = MarkdownParser().parse("![alt](src.png)")
    segmenter = MarkdownSegmenter()
    normalized = NormalizedContent(
        kind=ContentKind.MARKDOWN,
        mime_type="text/markdown",
        content=doc,
        source_uri="doc.md",
    )
    segments = segmenter.segment(normalized)
    assert len(segments) == 1
    assert segments[0].type == SegmentType.IMAGE


def test_pipeline_extracts_markdown_objects() -> None:
    artifact = Artifact(name="adr.md", relative_path="adr.md", mime_type="text/markdown")
    text = """# Use PostgreSQL

We will adopt PostgreSQL for reliability.

| Aspect | Value |
|--------|-------|
| Scale  | High  |
"""
    pipeline = ExtractionPipeline()
    result = pipeline.extract(artifact, text, project_id="akwb")
    assert result.ok
    assert len(result.objects) == 3
    titles = {obj.title for obj in result.objects}
    assert "Use PostgreSQL" in titles


def test_empty_markdown() -> None:
    doc = MarkdownParser().parse("")
    assert doc.children == []


def test_large_markdown() -> None:
    lines = [f"## Heading {i}\n\nParagraph {i}." for i in range(200)]
    text = "\n\n".join(lines)
    doc = MarkdownParser().parse(text)
    assert len([c for c in doc.children if c.type == "heading"]) == 200


def test_malformed_front_matter_keeps_raw() -> None:
    text = "---\nbroken: [\n---\n# Title"
    doc = MarkdownParser().parse(text)
    meta = [c for c in doc.children if c.type == "metadata"]
    assert len(meta) == 1
    assert "parse_error" in meta[0].metadata
