# Enterprise Extraction Pipeline

## Purpose

The `akwb.extraction` package converts discovered project artifacts into canonical `KnowledgeObject` instances using a clean, multi-stage, plugin-extensible pipeline. It intentionally contains no AI-specific business logic, no report generation, and no publishing logic; it only transforms content into knowledge objects.

## Pipeline Stages

```
Artifact
    ↓
Reader
    ↓
CanonicalDocument  (for document content) / NormalizedContent
    ↓
CanonicalValidator
    ↓
Segmentation Engine
    ↓
list[Segment]
    ↓
Extractor
    ↓
list[ExtractionCandidate]
    ↓
CandidateValidator
    ↓
CandidateBuilder
    ↓
KnowledgeObject
    ↓
KnowledgeFramework.validate_object
```

## Domain Model

- `NormalizedContent` — a uniform wrapper around raw artifact content (text, binary, structured, document, multimodal). For document content it wraps a `CanonicalDocument`.
- `CanonicalDocument` — the single parser-agnostic document AST built from `DocumentElement`s; produced by `DocumentReader` implementations, validated by `CanonicalValidator`, and segmented by `CanonicalSegmenter`.
- `DocumentElement` — a typed, recursive node in a `CanonicalDocument`.
- `CanonicalValidationResult` — the outcome of validating a `CanonicalDocument` before extraction.
- `Segment` — a typed, contiguous fragment of normalized content: heading, paragraph, code, table, structural, semantic, adaptive, document.
- `ExtractionCandidate` — a pre-object carrying a proposed knowledge type, title, description, content, source, evidence, and confidence.
- `ExtractionResult` — the final bundle of `KnowledgeObject`s plus diagnostics and candidate count.

## Plugin Ports

The pipeline exposes five plugin ports, all extending `PluginPort`:

- `Reader` (`port_name = "reader"`) — converts an `Artifact` + bytes/string into `NormalizedContent`.
- `Segmenter` (`port_name = "segmenter"`) — splits `NormalizedContent` into `Segment`s.
- `Extractor` (`port_name = "extractor"`) — maps `Segment`s to `ExtractionCandidate`s.
- `CandidateBuilder` (`port_name = "candidate_builder"`) — builds a `KnowledgeObject` from a candidate.
- `CandidateValidator` (`port_name = "candidate_validator"`) — validates an `ExtractionCandidate` before it is built.

## Built-in Readers

| Reader | MIME types | Output |
|---|---|---|
| `MarkdownReader` | `text/markdown`, `text/x-markdown` | `NormalizedContent(kind=DOCUMENT, content=CanonicalDocument)` |
| `TextReader` | `text/*` | `NormalizedContent(kind=TEXT, content=str)` |
| `BinaryReader` | `image/*`, `audio/*`, `video/*`, `application/octet-stream` | `NormalizedContent(kind=BINARY, content=bytes)` |
| `StructuredReader` | `application/json`, `application/x-yaml`, `application/yaml`, `text/yaml` | `NormalizedContent(kind=STRUCTURED, content=dict/list)` |

## Built-in Segmenters

| Segmenter | Handles | Notes |
|---|---|---|
| `HeadingSegmenter` | text | ATX (`#`) and Setext (`====`, `----`) headings. |
| `ParagraphSegmenter` | text | Blank-line-delimited paragraphs, skipping headings, code, and tables. |
| `CodeSegmenter` | text | Triple-backtick fenced code blocks. |
| `TableSegmenter` | text | Markdown-style pipe tables. |
| `StructuralSegmenter` | structured JSON/YAML | Recursively emits key/value and list-item segments. |
| `SemanticSegmenter` | text | Sentence-level segments. |
| `AdaptiveSegmenter` | all content kinds | Selects and runs the segmenters appropriate for the content kind, including `CanonicalSegmenter` for `DOCUMENT` content. |
| `CanonicalSegmenter` | document | Splits `CanonicalDocument` trees produced by `DocumentReader` implementations into `Segment`s. |

## Built-in Extractor

`RuleBasedExtractor` maps segments to candidates using a keyword-based heuristic (no AI):

- Headings → `decision`, `goal`, etc. based on keywords.
- Paragraphs / semantic sentences → `requirement`, `document`, etc.
- Code blocks → `component`.
- Tables → `business_rule`.
- Structural nodes → mapped by key label or `entity`.

## Built-in Builder

`DefaultKnowledgeObjectBuilder` converts a validated `ExtractionCandidate` into a `KnowledgeObject`, wiring the artifact source, creating a `KnowledgeEvidence` record from the candidate's excerpt and location, and applying project metadata.

## Built-in Candidate Validators

- `RequiredFieldsCandidateValidator` — ensures title and knowledge type are present.
- `RegisteredTypeCandidateValidator` — ensures the knowledge type is registered in the `KnowledgeFramework`.

## Canonical Validation Layer

`CanonicalValidator` sits between the Reader and the segmentation stage. It is run automatically by `ExtractionPipeline` whenever a reader produces `NormalizedContent(kind=DOCUMENT)`.

Responsibilities:

- Verify the root object is a `CanonicalDocument` of type `document`.
- Require `source_uri` and recommend `mime_type`.
- Validate that every `DocumentElement` has a non-empty, unique `id`.
- Validate element type and metadata shape.
- Enforce the allowed element hierarchy (for example, `table` may only contain `table_row`, `table_head`, and `table_body`).
- Reject malformed documents with clear diagnostics before extraction proceeds.

The validation layer ensures the extraction pipeline can trust every `CanonicalDocument` it receives.

## Usage Example

```python
from akwb.domain.models import Artifact
from akwb.extraction.pipeline import ExtractionPipeline

pipeline = ExtractionPipeline()

artifact = Artifact(
    name="adr.md",
    relative_path="docs/adr.md",
    mime_type="text/markdown",
)

text = """
# Decision to use PostgreSQL

We will use PostgreSQL as the primary data store.

```python
def connect():
    return psycopg2.connect(DSN)
```
"""

result = pipeline.extract(artifact, text, project_id="akwb")
print(f"Objects: {len(result.objects)}")
for obj in result.objects:
    print(f"- {obj.type}: {obj.title}")
```

## Plugin Example

For CSV and other non-document artifacts, extend `Reader` directly:

```python
from akwb.extraction.models import ContentKind, NormalizedContent
from akwb.extraction.plugins import Reader

class CsvReader(Reader):
    supported_mime_types = ("text/csv",)

    def read(self, artifact, content, context=None):
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        return NormalizedContent(
            kind=ContentKind.STRUCTURED,
            mime_type=artifact.mime_type,
            content={"rows": text.splitlines()},
            source_uri=artifact.relative_path or artifact.name,
        )

# In your plugin register function:
#   api.register_port("reader", CsvReader())
```

For document artifacts (HTML, DOCX, PDF, email, etc.), the only extension point is `DocumentReader`:

```python
from akwb.extraction.document import CanonicalDocument, DocumentElement, DocumentReader

class HtmlReader(DocumentReader):
    supported_mime_types = ("text/html",)

    def read_canonical(self, artifact, content, context=None):
        # Parse HTML into a CanonicalDocument tree.
        return CanonicalDocument(
            source_uri=artifact.relative_path or artifact.name,
            mime_type=artifact.mime_type,
            language="html",
            children=[
                DocumentElement(type="heading", level=1, content="Title"),
                DocumentElement(type="paragraph", content="..."),
            ],
        )
```

A `DocumentReader` never needs to know about segmenters, extractors, or knowledge generation. If it emits a valid `CanonicalDocument`, the pipeline will validate, segment, and extract it automatically.

## Module Structure

```
src/akwb/extraction/
  __init__.py        # Public API
  document.py        # Canonical Document Model + DocumentReader + CanonicalValidator + CanonicalSegmenter
  models.py          # NormalizedContent, Segment, ExtractionCandidate, ExtractionResult
  plugins.py         # Reader, Segmenter, Extractor, CandidateBuilder, CandidateValidator ports
  readers.py         # TextReader, BinaryReader, StructuredReader
  markdown.py        # MarkdownParser, MarkdownCanonicalMapper, MarkdownReader
  segmenters.py      # Heading, Paragraph, Code, Table, Structural, Semantic, Adaptive, Canonical segmenters
  extractors.py      # RuleBasedExtractor
  builders.py        # DefaultKnowledgeObjectBuilder and candidate validators
  pipeline.py        # ExtractionContext and ExtractionPipeline orchestrator
```

## Future Work

- Add streaming readers and segmenters for very large files.
- Pluggable candidate-resolution strategies (merging duplicate candidates, disambiguation).
- Confidence estimation beyond the default `1.0` algorithm score.
- Richer table/column extraction and relationship inference.
