# Traceability Model

## Purpose

Define how every piece of published content records its origin. The Traceability Model is a **cross-cutting domain concern**: every knowledge object, content block, generated document, and exported artifact must be able to answer "where did this come from?"

## Responsibilities

- Provide a portable, versioned `SourceReference` value object.
- Support source kinds from files, chat transcripts, AI models, email, images, and future connectors.
- Capture provenance at paragraph, section, and document granularity.
- Preserve traceability through document generation and export.
- Enable audit trails, confidence scoring, and attribution.

## Principles

- **Every paragraph knows its source.** Traceability is not optional and is not a document-level afterthought.
- **Source-kind agnostic.** The same model applies to Markdown, DOCX, ChatGPT output, code, and future connectors.
- **Non-destructive.** Exporters must preserve `SourceReference` information; they may render it as footnotes, comments, sidecars, or embedded metadata.
- **Evidence-based.** A reference may include a confidence score and a verbatim excerpt so it can be verified without opening the original file.

## Core Concepts

### `SourceReference` (Value Object)

| Field | Meaning |
|---|---|
| `id` | Stable reference URI (`source://<kind>/<path>#<span>`). |
| `kind` | `SourceKind` value. |
| `path` | Project-relative path, connector id, or external URI. |
| `span` | Optional location within the source (`line`, `character`, `section`, `timecode`). |
| `fingerprint` | Content hash of the referenced source at the time of reference. |
| `excerpt` | Optional short verbatim text used for verification. |
| `confidence` | 0.0–1.0 confidence that the reference points to the correct source. |
| `retrieved_at` | ISO timestamp when the reference was created. |

### `SourceKind` (Enumeration / Registry)

Source kinds are contributed by plugins and configuration. Core provides a registry and a set of default kinds.

| Kind | Description |
|---|---|
| `markdown` | Markdown files. |
| `docx` | Word documents. |
| `pdf` | PDF documents. |
| `txt` | Plain text files. |
| `html` | HTML pages. |
| `code` | Source code files (any language). |
| `chatgpt` | ChatGPT conversation exports or API responses. |
| `claude` | Claude conversation exports or API responses. |
| `gemini` | Gemini conversation exports or API responses. |
| `email` | Email messages. |
| `image` | Images and diagrams. |
| `spreadsheet` | CSV, Excel, etc. |
| `database` | Database tables or queries. |
| `issue` | Issue tracker entries. |
| `api` | REST/GraphQL/gRPC endpoint documentation. |
| `custom` | Any future connector-defined kind. |

> Custom kinds are registered by `SourceConnector` plugins through the `SourceKindRegistry`.

### `SourceSpan`

| Field | Meaning |
|---|---|
| `start` | Start location. |
| `end` | End location. |
| `unit` | `line`, `character`, `section`, `paragraph`, `page`, `timecode`. |

### `Provenance` (Value Object)

A chain of transformations from original sources to final content.

| Field | Meaning |
|---|---|
| `source_refs` | List of `SourceReference`s. |
| `generated_by` | Plugin or engine that produced the content. |
| `generated_at` | ISO timestamp. |
| `parent_provenance` | Optional `Provenance` of an upstream content block. |
| `transformations` | List of operations applied (`summarize`, `translate`, `merge`, `quote`, `infer`). |

### `ContentBlock`

A section, paragraph, or other atom of a `GeneratedDocument`.

| Field | Meaning |
|---|---|
| `id` | UUID. |
| `content_type` | `paragraph`, `heading`, `list`, `code`, `table`, `image`, `callout`. |
| `content` | Raw content (text, structured data, or reference to binary). |
| `provenance` | `Provenance` for this block. |
| `domain_tags` | Domains this block belongs to. |

## Traceability at Each Layer

### Discovery

- `ArtifactEntry` records `absolute_path` and `relative_path` as source metadata.
- `SourceCatalog` entries carry `SourceReference` objects for each file.

### Knowledge Extraction

- Every `KnowledgeUnit` and `Relationship` stores `source_refs`.
- `source_refs` include path, span, and fingerprint.

### Document Generation

- Each `ContentBlock` in a `GeneratedDocument` stores `Provenance`.
- `Provenance` references `KnowledgeObject`s, `SourceReference`s, or other `ContentBlock`s.
- A document-level `Provenance` aggregates all block-level sources.

### Export

- Exporters embed or sidecar traceability.
- Markdown exporters may render footnotes or HTML comments.
- JSON exporters include `provenance` fields.
- PDF/DOCX exporters may include metadata or comments.

## SourceConnector Plugin Port

For future source kinds (e.g., Slack, Notion, Jira), a `SourceConnector` plugin can normalize external content into `SourceReference`s.

```python
class SourceConnector(ABC):
    port_name: str = "source_connector"

    @property
    @abstractmethod
    def supported_kinds(self) -> list[str]:
        ...

    @abstractmethod
    def fetch(self, ref: SourceReference) -> str | bytes:
        """Return the source content for a reference."""
        ...

    @abstractmethod
    def normalize(self, raw: object) -> list[SourceReference]:
        """Convert raw connector data into canonical source references."""
        ...
```

## Traceability Enrichment

`TraceabilityEnricher` plugins may add `SourceReference`s to `ContentBlock`s or resolve indirect references (e.g., a requirement that references a test file).

```python
class TraceabilityEnricher(ABC):
    port_name: str = "traceability_enricher"

    @abstractmethod
    def enrich(self, block: ContentBlock, catalog: KnowledgeObjectCatalog) -> list[SourceReference]:
        ...
```

## Confidence and Attribution

- `SourceReference.confidence` is set by the component that created the reference.
- `Provenance.transformations` records whether content was quoted, summarized, translated, or inferred.
- `ContentBlock` that is purely AI-generated must still cite the knowledge sources used; the model itself is recorded in `generated_by`.

## Storage of Traceability

- `SourceReference` and `Provenance` are serialized as JSON objects inside `KnowledgeUnit`, `Relationship`, and `ContentBlock` records.
- Large provenance graphs are stored as `trace_index.jsonl` or inside `graph_index.sqlite` to avoid bloating main JSONL files.
- Exporters decide how to render; core never loses the raw data.

## Inputs

- `SourceCatalog` and `KnowledgeGraph`.
- `GeneratedDocument` content blocks.
- `SourceConnector` and `TraceabilityEnricher` plugins.

## Outputs

- `ContentBlock` objects with `Provenance`.
- `SourceReference` indexes.
- `TraceabilityPreserved` diagnostics from exporters.

## Dependencies

- `PUBLISHING_ARCHITECTURE.md`
- `PUBLISHING_PIPELINE.md`
- `EXPORT_ARCHITECTURE.md`
- `../04_DOMAIN_MODEL.md`

## Future Extensions

- Verifiable references using content-addressable hashes.
- Time-machine references to historical file versions.
- Cross-project traceability linking.
- Graph traversal queries: "find all documents that depend on this requirement."

## Risks

- Verbose traceability can bloat artifacts.
- AI-generated content may cite many sources; summarization may lose fine-grained references.
- External connectors may fail to resolve, producing dangling references.

## Design Decisions

- **Traceability is a value object, not an engine.** It is owned by `ContentBlock`, `KnowledgeUnit`, and `Relationship`.
- **Source kinds are a registry, not an enum.** New kinds are added by plugins without core changes.
- **Provenance is a chain.** Each transformation links to its parent, enabling full audit trails.
- **Exporters must validate traceability preservation.** The `ExportResult` includes a `traceability_preserved` flag.
