# Enterprise Markdown AST Parser

The Enterprise Markdown AST Parser is the first concrete parser for the AKWB
Extraction Pipeline. It parses Markdown files into a typed, source-mapped AST
and feeds the existing extraction pipeline without modifying the Knowledge
Framework or Graph Engine.

## Purpose

- Parse Markdown using a real AST-producing library (`markdown-it-py` with GFM
  extensions).
- Expose an `AST walker` and `AST visitor` for custom analysis.
- Map the AST to `NormalizedContent` so that built-in segmenters and extractors
  can work with rich Markdown elements.
- Serve as the reference architecture for all future parsers.

## Architecture

```
Markdown file
    |
    v
MarkdownReader (Reader plugin)
    |
    v
MarkdownParser -> MarkdownDocument (MarkdownNode tree)
    |
    v
MarkdownASTMapper -> NormalizedContent(kind=ContentKind.MARKDOWN)
    |
    v
MarkdownSegmenter -> Segment(HEADING, PARAGRAPH, CODE, TABLE, LIST,
                              TASK_LIST, QUOTE, HTML, FOOTNOTE, METADATA, ...)
    |
    v
ExtractionPipeline extractors and builders -> KnowledgeObject
```

## Components

### `MarkdownNode`

Typed AST node:

- `type`: node kind (`heading`, `paragraph`, `list`, `table`, `code`, `quote`,
  `link`, `image`, `html`, `footnote`, `metadata`, ...).
- `tag`: underlying HTML tag when applicable.
- `level`: heading level or list nesting.
- `content`: text, rows, or raw content depending on node type.
- `attrs`: link hrefs, image src, table cell attributes.
- `location`: `{"start_line": int, "end_line": int}` source mapping.
- `metadata`: extra metadata such as language, checked state, front-matter flags.
- `children`: nested `MarkdownNode` objects.

### `MarkdownDocument`

Root node that holds top-level children and document-level metadata extracted
from YAML front matter.

### `MarkdownParser`

Wraps `MarkdownIt` with the `gfm_plugin` (tables, task lists, strikethrough,
autolinks, alerts, footnotes) and optional YAML front matter. Produces a
`MarkdownDocument`.

### `MarkdownASTWalker` / `MarkdownASTVisitor`

Generic depth-first traversal and visitor dispatch:

```python
class Counter(MarkdownASTVisitor):
    def __init__(self) -> None:
        self.heading_count = 0

    def visit_heading(self, node: MarkdownNode) -> None:
        self.heading_count += 1

    def visit_default(self, node: MarkdownNode) -> None:
        pass

MarkdownASTWalker().walk(document, Counter())
```

### `MarkdownASTMapper`

Converts parsed Markdown text into `NormalizedContent` with
`kind=ContentKind.MARKDOWN`.

### `MarkdownReader`

`Reader` plugin registered in `ExtractionPipeline` for `text/markdown` and
`text/x-markdown` artifacts.

### `MarkdownSegmenter`

`Segmenter` plugin that walks the AST and emits typed `Segment` objects for the
pipeline.

## Supported Markdown Elements

- Headings (ATX and setext)
- Paragraphs with inline formatting
- Ordered and unordered lists
- Task lists (`- [x] task`)
- Nested lists
- Blockquotes
- Fenced code blocks with language info
- Tables (GFM)
- Links and images
- Raw HTML blocks
- Footnotes
- YAML front matter / metadata
- Source locations for block nodes

## Usage

```python
from akwb.domain.models import Artifact
from akwb.extraction.pipeline import ExtractionPipeline

artifact = Artifact(
    name="adr.md",
    relative_path="docs/adr.md",
    mime_type="text/markdown",
)

text = """# Use PostgreSQL

We will adopt PostgreSQL.

- Scalable
- [x] Reviewed

| Criterion | PostgreSQL |
|-----------|------------|
| Scale     | High       |
"""

pipeline = ExtractionPipeline()
result = pipeline.extract(artifact, text, project_id="akwb")
print(result.ok, len(result.objects))
for obj in result.objects:
    print(obj.type, obj.title)
```

## Direct AST access

```python
from akwb.extraction.markdown import MarkdownParser, MarkdownSegmenter
from akwb.extraction.models import ContentKind, NormalizedContent

parser = MarkdownParser()
doc = parser.parse(text, source_uri="doc.md")

segmenter = MarkdownSegmenter()
segments = segmenter.segment(
    NormalizedContent(
        kind=ContentKind.MARKDOWN,
        mime_type="text/markdown",
        content=doc,
        source_uri="doc.md",
    )
)
```

## Module structure

- `src/akwb/extraction/markdown.py` — parser, AST, walker, visitor, mapper,
  reader, and segmenter.
- `tests/unit/extraction/test_markdown.py` — unit tests.
- `tests/integration/extraction/test_markdown_files.py` — file-based
  integration tests.
- `docs/MARKDOWN_AST_PARSER.md` — this document.
- `examples/markdown_parser_example.py` — runnable example.
