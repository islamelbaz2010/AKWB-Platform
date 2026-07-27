# AKWB Minimum Viable Engine (MVE) Definition

## Purpose

Define the smallest complete version of AKWB that can be reused by downstream
products. The MVE must be able to analyze a real software project, produce a
validated `KnowledgeGraph`, persist it to `.akwb/`, and expose it through stable
exports.

## MVE Success Criteria

A downstream product must be able to:

1. Install AKWB as a Python package.
2. Run `akwb init` and `akwb analyze <path>` on a project.
3. Find a `KnowledgeGraph` serialized under `.akwb/knowledge/`.
4. Read graph exports in JSONL, DOT, and Cypher from `.akwb/graph/`.
5. Register a local plugin that adds a parser or extractor.

## In Scope

### 1. End-to-End Analysis Command

`akwb analyze <path>` must:

- Initialize the workspace if missing.
- Run discovery to produce a `SourceCatalog`.
- Select a reader/parser per file type.
- Run extraction to produce `KnowledgeObject` candidates.
- Build a `KnowledgeGraph` from the catalog.
- Validate the graph.
- Persist all artifacts to `.akwb/`.
- Return a structured exit code and summary.

### 2. Discovery

- File scanning with ignore patterns.
- Classification of Markdown, Python, JSON, YAML, and plain-text files.
- SHA-256 fingerprinting with mtime/size quick-skip.
- Incremental change detection.
- Artifact registry persistence.

### 3. Parsing

- **Markdown AST Parser** (built-in).
- **Python AST Parser** (built-in, minimal): modules, classes, functions,
  methods, imports, docstrings.
- **Structured Reader** for JSON/YAML.
- **Text Reader** for unknown text files.
- **Binary Reader** for unsupported binary files (stores metadata only).

### 4. Extraction

- Rule-based extractor mapping headings/paragraphs/code/tables to knowledge types.
- Python-specific extractor mapping AST nodes to `component`, `function`, `class`,
  `dependency`, etc.
- Built-in candidate validators.
- Default knowledge object builder wiring sources and evidence.

### 5. Knowledge Object Framework

- All built-in types, relationship types, and evidence types.
- Catalog creation and validation.
- Serialization to JSON, JSONL, YAML.

### 6. Knowledge Graph Engine

- Graph build from catalog.
- In-memory index and query engine.
- Traversal (ancestors, descendants, dependency, reverse-dependency, shortest
  path).
- Graph validation (broken refs, cycles, orphans, duplicate edges).
- Graph statistics.

### 7. Graph Persistence

- `LocalGraphStorage` backend implementing the `GraphStorage` port.
- Writes `graph_nodes.jsonl`, `graph_edges.jsonl`, `graph.dot`, `graph.cypher`
  to `.akwb/graph/`.
- Loads graph from JSONL for `akwb report`/`akwb status`.

### 8. Workspace & Storage

- `.akwb/` bootstrap with `workspace.json`.
- Local storage backend with path sandboxing and atomic writes.
- Source catalog persistence at `.akwb/index/source_catalog.jsonl`.
- Knowledge catalog persistence at `.akwb/knowledge/`.
- Logs at `.akwb/logs/`.

### 9. CLI

- `akwb version`
- `akwb init [--force]`
- `akwb doctor`
- `akwb analyze [--force] [--depth minimal|standard|deep]`
- `akwb report [summary|structure|graph]`
- `akwb export [jsonl|dot|cypher]`
- `akwb clean [--cache-only|--all]`

### 10. Plugin Framework

- Local plugin directory loading.
- `reader`, `segmenter`, `extractor`, `candidate_builder`, `candidate_validator`
  ports.
- `knowledge_type_provider`, `relationship_type_provider`,
  `evidence_type_provider`, `knowledge_validator_provider` ports.
- `graph_storage`, `graph_query_engine`, `graph_traversal`, `graph_index` ports.
- Plugin API compatibility check (`plugin_api_version == "1"`).

## Out of Scope

- AI summarization, chunking, embeddings, RAG, vector indexes.
- Plugin marketplace or remote plugin install.
- Web dashboard, IDE UI, chat UI.
- Publishing platform / site generation.
- Workflow automation / approval workflows.
- Multi-project federation or cloud hosting.
- Advanced source-code analysis (type inference, call-graph resolution across
  dynamic languages, runtime traces).
- Marketplace signing and sandboxing beyond path validation.

## Core Modules Required

```
akwb
├── cli.py                  # CLI entry and commands
├── config.py               # Configuration loading and validation
├── container.py            # DI composition root
├── types.py                # Shared result and diagnostic types
├── discovery/              # Scan, classify, fingerprint, incremental
├── storage/                # LocalStorageBackend, UnitOfWork
├── workspace/              # WorkspaceBootstrap
├── extraction/             # Pipeline, readers, segmenters, extractors, builders
├── knowledge/              # Framework, models, validation, serialization
├── graph/                  # Graph model, index, query, traversal, stats, persistence
├── plugins/                # Loader, registry, manifest
├── events/                 # InMemoryEventBus
└── observability/          # LoggerObservability
```

## Required APIs

### Programmatic

- `DiscoveryEngine.discover(project_root) -> Result[ArtifactRegistry, Diagnostic]`
- `ExtractionPipeline.extract(artifact, content, ...) -> ExtractionResult`
- `KnowledgeFramework.new_catalog(...) -> KnowledgeCatalog`
- `GraphEngine.build(catalog) -> KnowledgeGraph`
- `GraphEngine.query(graph, query) -> QueryResult`
- `GraphEngine.traverse(graph, request) -> TraversalResult`
- `GraphEngine.validate(graph) -> ValidationResult`
- `GraphEngine.statistics(graph) -> GraphStatisticsResult`
- `GraphEngine.save(graph, target) -> Any` (via `GraphStorage`)
- `GraphEngine.load(source) -> KnowledgeGraph` (via `GraphStorage`)

### CLI

- `akwb analyze <path>` with `--force` and `--depth`.
- `akwb report <name>` producing `.akwb/reports/`.
- `akwb export <format>` producing `.akwb/graph/`.

## Required Plugins

| Plugin | Port | Purpose |
|---|---|---|
| `MarkdownReader` | `reader` | Parse Markdown files into AST. |
| `MarkdownSegmenter` | `segmenter` | Segment Markdown AST into pipeline segments. |
| `PythonReader` | `reader` | Parse Python files into AST. |
| `PythonSegmenter` | `segmenter` | Segment Python AST. |
| `PythonExtractor` | `extractor` | Extract components, functions, classes, imports. |
| `RuleBasedExtractor` | `extractor` | Extract knowledge from Markdown/text segments. |
| `DefaultKnowledgeObjectBuilder` | `candidate_builder` | Build `KnowledgeObject`s. |
| `LocalGraphStorage` | `graph_storage` | Persist/load graph from `.akwb/`. |

## Required Exports

The MVE must write these artifacts for downstream products:

| Artifact | Path | Format |
|---|---|---|
| Workspace manifest | `.akwb/workspace.json` | JSON |
| Source catalog | `.akwb/index/source_catalog.jsonl` | JSONL |
| Knowledge catalog | `.akwb/knowledge/catalog.json` | JSON |
| Graph nodes | `.akwb/knowledge/graph_nodes.jsonl` | JSONL |
| Graph edges | `.akwb/knowledge/graph_edges.jsonl` | JSONL |
| Graph export (lineage) | `.akwb/graph/graph.jsonl` | JSONL |
| Graph export (visual) | `.akwb/graph/graph.dot` | DOT |
| Graph export (query) | `.akwb/graph/graph.cypher` | Cypher |
| Analysis summary | `.akwb/reports/summary.md` | Markdown |
| Analysis summary | `.akwb/reports/summary.json` | JSON |
| Analysis log | `.akwb/logs/analysis.log` | Text |

## Acceptance Test

A project with the following structure:

```
myproject/
  README.md
  src/
    app.py
  tests/
    test_app.py
```

After `akwb analyze myproject` must produce:

- `.akwb/workspace.json` with `schema_version` and `project_root`.
- `.akwb/index/source_catalog.jsonl` containing `README.md`, `app.py`,
  `test_app.py`.
- `.akwb/knowledge/graph_nodes.jsonl` containing at least one `document`,
  one `component`, and one `function`.
- `.akwb/knowledge/graph_edges.jsonl` containing a `contains` or `depends_on`
  edge between `app.py` and at least one function/class.
- `.akwb/graph/graph.dot` with a non-empty graph body.

## Exclusions from MVE

- No AI model calls.
- No embeddings or vector indexes.
- No marketplace.
- No web UI.
- No publishing beyond raw exports.
- No real-time watch mode.
- No multi-project federation.

## Why This Is the Minimum

Without end-to-end `analyze`, the engine is only a library. Without a code
parser, the engine cannot analyze the primary input of software projects.
Without graph persistence, downstream products cannot consume the graph.
Without exports, the engine cannot be reused. The features listed above are the
smallest set that satisfies the original product vision.
