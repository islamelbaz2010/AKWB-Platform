"""Usage example for the Enterprise Markdown AST Parser."""

from __future__ import annotations

from akwb.domain.models import Artifact
from akwb.extraction.markdown import MarkdownParser, MarkdownSegmenter
from akwb.extraction.models import ContentKind, NormalizedContent
from akwb.extraction.pipeline import ExtractionPipeline


def main() -> None:
    artifact = Artifact(
        name="adr.md",
        relative_path="docs/adr/001-postgresql.md",
        mime_type="text/markdown",
    )

    text = """---
title: ADR-001
tags: [database, decision]
---
# Decision to use PostgreSQL

We will adopt PostgreSQL as the primary data store for reliability.

- Scalable
- [x] Reviewed
- [ ] Needs monitoring

> This is a long-term strategic decision.

```python
def connect():
    return psycopg2.connect(DSN)
```

| Criterion | PostgreSQL |
|-----------|------------|
| Scale     | High       |

See [PostgreSQL docs](https://www.postgresql.org) for details.
"""

    # Direct AST usage
    parser = MarkdownParser()
    document = parser.parse(text, source_uri=artifact.relative_path)
    print(f"Document children: {len(document.children)}")
    print(f"Front matter title: {document.metadata.get('title')}")

    # Segment AST
    segmenter = MarkdownSegmenter()
    normalized = NormalizedContent(
        kind=ContentKind.MARKDOWN,
        mime_type=artifact.mime_type,
        content=document,
        source_uri=artifact.relative_path or artifact.name,
    )
    segments = segmenter.segment(normalized)
    print(f"Segments: {len(segments)}")
    for segment in segments:
        print(f"  - {segment.type}: {str(segment.content)[:60]}")

    # Pipeline extraction
    pipeline = ExtractionPipeline()
    result = pipeline.extract(artifact, text, project_id="akwb")
    print(f"\nExtraction OK: {result.ok}")
    print(f"Objects: {len(result.objects)}")
    for obj in result.objects:
        print(f"  - {obj.type}: {obj.title}")

    if result.diagnostics:
        print("\nDiagnostics:")
        for diag in result.diagnostics:
            print(f"  - [{diag.level}] {diag.code}: {diag.message}")


if __name__ == "__main__":
    main()
