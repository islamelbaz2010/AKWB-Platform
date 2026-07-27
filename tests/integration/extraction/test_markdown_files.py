"""Integration tests for the Markdown parser with real files."""

from pathlib import Path

from akwb.domain.models import Artifact
from akwb.extraction.markdown import MarkdownParser, MarkdownSegmenter
from akwb.extraction.models import ContentKind, NormalizedContent
from akwb.extraction.pipeline import ExtractionPipeline


def _write_and_read(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return path.read_text(encoding="utf-8")


def test_nested_headings_file(tmp_path: Path) -> None:
    file_path = tmp_path / "nested.md"
    text = _write_and_read(
        file_path,
        """# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
""",
    )
    doc = MarkdownParser().parse(text, source_uri=str(file_path))
    headings = [n for n in doc.children if n.type == "heading"]
    assert len(headings) == 6
    levels = [h.level for h in headings]
    assert levels == [1, 2, 3, 4, 5, 6]


def test_table_file(tmp_path: Path) -> None:
    file_path = tmp_path / "table.md"
    text = _write_and_read(
        file_path,
        """# Comparison

| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
| 4 | 5 | 6 |
""",
    )
    artifact = Artifact(
        name="table.md", relative_path="table.md", mime_type="text/markdown"
    )
    result = ExtractionPipeline().extract(artifact, text)
    assert result.ok
    assert any("Comparison" in obj.title for obj in result.objects)
    assert any(obj.type == "business_rule" for obj in result.objects)


def test_code_file(tmp_path: Path) -> None:
    file_path = tmp_path / "code.md"
    text = _write_and_read(
        file_path,
        """# Setup

```python
def configure():
    return {"ok": True}
```
""",
    )
    artifact = Artifact(
        name="code.md", relative_path="code.md", mime_type="text/markdown"
    )
    result = ExtractionPipeline().extract(artifact, text)
    assert result.ok
    assert any(obj.type == "component" for obj in result.objects)


def test_mixed_content_file(tmp_path: Path) -> None:
    file_path = tmp_path / "mixed.md"
    text = _write_and_read(
        file_path,
        """---
title: Mixed Document
tags: [one, two]
---
# Decision to use PostgreSQL

We will adopt PostgreSQL as the primary data store.

- Scalable
- [x] Reviewed
- [ ] Needs monitoring

> This is a strategic decision.

```python
def connect():
    return psycopg2.connect(DSN)
```

| Criterion | PostgreSQL |
|-----------|------------|
| Scale     | High       |

See [PostgreSQL docs](https://postgresql.org) for details.
""",
    )
    artifact = Artifact(
        name="mixed.md", relative_path="mixed.md", mime_type="text/markdown"
    )
    result = ExtractionPipeline().extract(artifact, text, project_id="akwb")
    assert result.ok
    assert len(result.objects) >= 4
    types = {obj.type for obj in result.objects}
    assert "decision" in types
    assert "document" in types
    assert "business_rule" in types
    assert "component" in types


def test_large_file(tmp_path: Path) -> None:
    file_path = tmp_path / "large.md"
    lines = [f"## Section {i}\n\nParagraph {i}." for i in range(500)]
    text = _write_and_read(file_path, "\n\n".join(lines))
    doc = MarkdownParser().parse(text, source_uri=str(file_path))
    headings = [n for n in doc.children if n.type == "heading"]
    assert len(headings) == 500
    segmenter = MarkdownSegmenter()
    normalized = NormalizedContent(
        kind=ContentKind.MARKDOWN,
        mime_type="text/markdown",
        content=doc,
        source_uri=str(file_path),
    )
    segments = segmenter.segment(normalized)
    assert len(segments) == 1000


def test_edge_case_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.md"
    text = _write_and_read(file_path, "")
    artifact = Artifact(
        name="empty.md", relative_path="empty.md", mime_type="text/markdown"
    )
    result = ExtractionPipeline().extract(artifact, text)
    assert result.ok
    assert result.objects == []


def test_edge_case_whitespace_only(tmp_path: Path) -> None:
    file_path = tmp_path / "whitespace.md"
    text = _write_and_read(file_path, "   \n\n   \n")
    artifact = Artifact(
        name="whitespace.md", relative_path="whitespace.md", mime_type="text/markdown"
    )
    result = ExtractionPipeline().extract(artifact, text)
    assert result.ok
    assert result.objects == []


def test_edge_case_malformed_front_matter(tmp_path: Path) -> None:
    file_path = tmp_path / "bad_front.md"
    text = _write_and_read(
        file_path,
        """---
not yaml: [
---
# Title
""",
    )
    doc = MarkdownParser().parse(text, source_uri=str(file_path))
    assert any(n.type == "metadata" for n in doc.children)
    assert any(n.type == "heading" for n in doc.children)


def test_edge_case_html_block(tmp_path: Path) -> None:
    file_path = tmp_path / "html.md"
    text = _write_and_read(file_path, "<div class='note'>HTML note</div>")
    doc = MarkdownParser().parse(text, source_uri=str(file_path))
    html_nodes = [n for n in doc.children if n.type == "html"]
    assert len(html_nodes) == 1
