# Product Boundary Review

**Status:** STOP — implementation freeze pending review approval.

## 1. Product Purpose

AKWB is a reusable **Enterprise Knowledge Extraction Engine**. It receives raw
enterprise information (primarily software project artifacts), converts it into
canonical **Knowledge Objects**, builds a reusable **Knowledge Graph**, and
exposes the result through stable APIs and exports. It is consumed by other
products, not by end users directly.

### What AKWB Is

- A CLI-driven, local-first, project-owned knowledge engine.
- A discovery engine that scans project files and builds a `SourceCatalog`.
- A parser framework that converts source files into normalized content.
- An extraction pipeline that derives typed `KnowledgeObject`s from content.
- A knowledge object framework with types, relationships, evidence, and validation.
- A knowledge graph engine with indexing, query, traversal, validation, and statistics.
- A workspace generator that persists results into a project-owned `.akwb/` directory.
- An export producer that writes graph and report artifacts in standard formats
  (JSONL, JSON, YAML, DOT, Cypher).
- A plugin framework that allows third-party parsers, extractors, relationship
  builders, and graph backends to extend the engine without core changes.

### What AKWB Is Not

- Not an AI chat or conversation product.
- Not a workspace visualization dashboard.
- Not a publishing platform or site generator.
- Not a prompt management tool.
- Not an agent runtime or workflow automation system.
- Not a business analytics portal or CRM.
- Not a memory UI for end users.
- Not an IDE plugin with UI panels.
- Not a multi-tenant SaaS with billing and SSO.
- Not a plugin marketplace or distribution service.

AKWB produces artifacts. Downstream products consume those artifacts to create
user experiences.

## 2. Product Boundaries

### Table A — Inside AKWB

| Capability | Why It Belongs Inside | Evidence |
|---|---|---|
| **Discovery** | The engine must know what sources exist and how to classify them. | `src/akwb/discovery/engine.py`, `docs/07_DISCOVERY_ENGINE.md` |
| **Fingerprinting & Incrementality** | Re-analysis must skip unchanged sources. | `src/akwb/discovery/fingerprint.py`, `src/akwb/discovery/incremental.py` |
| **File Classification** | Sources must be routed to the correct parser. | `src/akwb/discovery/classifier.py` |
| **Ignore Patterns** | The engine must avoid `.git`, build artifacts, and dependencies. | `src/akwb/discovery/ignore.py` |
| **Parser Framework (Reader / Segmenter)** | Normalized parsing is core to extraction. | `src/akwb/extraction/plugins.py`, `src/akwb/extraction/readers.py`, `src/akwb/extraction/segmenters.py` |
| **Markdown AST Parser** | First concrete parser; produces rich AST segments. | `src/akwb/extraction/markdown.py`, `docs/MARKDOWN_AST_PARSER.md` |
| **Rule-Based Extractor** | MVP extraction of candidates from segments. | `src/akwb/extraction/extractors.py` |
| **Knowledge Object Framework** | Canonical domain model and validation. | `src/akwb/knowledge/`, `docs/KNOWLEDGE_OBJECT_FRAMEWORK.md` |
| **Knowledge Graph Engine** | Graph construction, query, traversal, validation, statistics. | `src/akwb/graph/`, `docs/KNOWLEDGE_GRAPH_ENGINE.md` |
| **Workspace Bootstrap** | Create `.akwb/` and write the manifest. | `src/akwb/workspace/bootstrap.py` |
| **Local Storage Backend** | Persist workspace artifacts with path sandboxing and atomic writes. | `src/akwb/storage/local.py` |
| **Configuration Loading** | Merge defaults, files, env vars, and CLI flags. | `src/akwb/config.py` |
| **CLI (init, doctor, analyze, status, config, report, clean, version)** | Engine control surface. | `src/akwb/cli.py`, `docs/13_CLI_SPECIFICATION.md` |
| **Plugin Loader & Registry** | Load local plugins and resolve ports. | `src/akwb/plugins/loader.py`, `src/akwb/plugins/registry.py` |
| **Export API (JSONL, JSON, YAML, DOT, Cypher)** | Downstream products need stable data formats. | `docs/11_DATA_MODEL.md`, `src/akwb/knowledge/serialization.py` |
| **Diagnostics & Observability** | Engine must report failures and progress. | `src/akwb/observability/`, `src/akwb/types.py` |
| **Event Bus (minimal)** | Decouples discovery, workspace, and extraction events. | `src/akwb/events/`, `src/akwb/domain/events.py` |

### Table B — Outside AKWB

| Capability | Why It Is Outside AKWB | Downstream Owner |
|---|---|---|
| **AI Chat UI** | Chat is a product experience, not an extraction concern. | Eunoia AI OS |
| **Workspace Dashboard / Visualizer** | Graph visualization and exploration are UI products. | StayOS or a dedicated dashboard product |
| **Publishing Platform** | Turning `.akwb/` exports into a publishable site is a separate product. | EPOS |
| **Prompt Management UI** | Prompt authoring, versioning, and testing are AI-product concerns. | AI Context Builder |
| **Agent Runtime** | Executing agents, tool chains, or workflows requires runtime state. | Eunoia AI OS |
| **Business Dashboards** | Executive metrics and analytics are product-specific. | Downstream analytics product |
| **Workflow Automation** | Approval, review, and lifecycle workflows are business-process products. | Downstream BPM / collaboration product |
| **Memory UI** | User-facing memory search and conversation history are AI-OS features. | Eunoia AI OS |
| **CRM / HRMS Integration** | Business system integrations belong in downstream adapters. | Relevant downstream product |
| **IDE-specific UI Panels** | IDEs consume `.akwb/`; they should render their own UI. | IDE plugins (not AKWB core) |
| **Model Training / Fine-tuning** | Training infrastructure is unrelated to extraction. | MLOps / AI product |
| **Multi-tenant SaaS Operations** | Hosting, billing, and tenant management are platform concerns. | Cloud AKWB service (if any) |
| **Plugin Marketplace** | Signed distribution and discovery are ecosystem services, not the engine. | Marketplace product |
| **Real-time Collaboration / Chat** | Multi-user editing and chat are product features. | Collaboration product |
| **Authentication / SSO for End Users** | Identity is a per-product decision. | Each downstream product |
| **Custom Report Templates as a Product** | AKWB produces raw reports; downstream products style and publish them. | EPOS / dashboard product |
| **Embeddings & RAG UI** | Vector search UI belongs to AI products. | AI Context Builder / Eunoia AI OS |

## 3. Overlap Analysis

The completed sprints built several capabilities that downstream products are
likely to also build. The following clarifies ownership.

### Eunoia AI OS

- **Overlap risk:** Memory, context bundles, summarization, chat, agent runtime.
- **AKWB boundary:** AKWB produces a `KnowledgeGraph`, source evidence, and
  context-structured exports. It does not maintain conversation history,
  memory state, or agent execution.
- **Recommendation:** Eunoia AI OS consumes `.akwb/knowledge/` and
  `.akwb/context/` artifacts. Remove the planned **AI Engine** from AKWB core;
  keep only the ability to export graph data in a context-friendly format.

### EPOS

- **Overlap risk:** Publishing, report generation, human-readable documentation.
- **AKWB boundary:** AKWB can write Markdown and JSON reports from the graph, but
  it does not publish a site, apply themes, or manage publish workflows.
- **Recommendation:** EPOS reads `.akwb/reports/` and `.akwb/graph/` exports.
  AKWB should stop at raw report artifacts.

### AI Context Builder

- **Overlap risk:** Chunking, embeddings, context bundles, prompt assembly,
  model-specific formatting.
- **AKWB boundary:** AKWB can produce a `ContextBundle` structure, but any
  model-specific tokenization, embedding, and prompt management belongs to AI
  Context Builder.
- **Recommendation:** Defer the full AI Engine. Export graph nodes/edges and
  summaries as JSONL; let AI Context Builder build embeddings and chunks.

### StayOS

- **Overlap risk:** Workspace status, project overview, productivity dashboards.
- **AKWB boundary:** AKWB writes `workspace.json`, source catalog, and graph
  artifacts. StayOS consumes them for its UI.
- **Recommendation:** StayOS reads `.akwb/`; AKWB does not render dashboards.

### Duplication Within AKWB

- **Rule-based extraction vs. parser AST extraction:** The text segmenters
  (`HeadingSegmenter`, `ParagraphSegmenter`, `CodeSegmenter`, `TableSegmenter`)
  are regex-based and overlap with what AST parsers (e.g., the Markdown parser)
  can do more accurately. For MVP, keep them as fallbacks for plain text files,
  but prefer AST parsers for known formats.
- **Graph engine vs. knowledge framework validation:** The knowledge framework
  validates objects/relationships; the graph engine validates graph structure.
  This is acceptable separation of concerns.
- **Workspace engine vs. storage backend:** The workspace bootstrap creates
  directories; the storage backend writes files. These can be merged into a
  single workspace persistence service. Impact: medium simplification.

## 4. Current State Assessment

| Sprint | Theme | Assessment | Rationale |
|---|---|---|---|
| **Sprint 1 — Foundation** | Config, CLI, container, storage, events, observability, plugins | **Essential / Slightly Over-Engineered** | The DI container, plugin loader, event bus, and observability are well-built, but the `Container` does not yet wire extraction or graph engines. The plugin framework is good; unit-of-work is underused. |
| **Sprint 2 — Discovery** | Scanning, classification, fingerprinting, incremental, artifact registry | **Essential** | `DiscoveryEngine.discover()` works end-to-end and CLI `akwb discover` is functional. This is core to the engine. |
| **Sprint 3 — Knowledge Object Framework** | Domain model, types, relationships, validation, serialization | **Essential** | Strong, well-tested framework. `KnowledgeFramework` is the heart of the canonical model. |
| **Sprint 4 — Extraction Pipeline** | Reader, segmenter, extractor, builder, pipeline | **Essential but Not Wired** | `ExtractionPipeline` works as a library, but it is not invoked by the CLI or container. It lacks relationship extraction. |
| **Sprint 5 — Knowledge Graph Engine** | Graph model, index, query, traversal, validation, stats | **Useful / Not Wired** | Graph engine is robust but not connected to extraction or workspace persistence. It needs a `GraphStorage` backend. |
| **Sprint 6 — Markdown AST Parser** | Markdown parser, AST, visitor, mapper, reader, segmenter | **Essential** | First real parser. Well-integrated into extraction pipeline. Good reference architecture. |

**Overall conclusion:** The engine components are individually sound, but they
are not yet assembled into a single `akwb analyze` command. That is the primary
gap.

## 5. Gap Analysis

Only gaps that are **required** before AKWB is a production-ready engine.

| # | Gap | Why Required | Evidence |
|---|---|---|---|
| 1 | **End-to-end `akwb analyze` command** | Without it, no user can run the full engine. The CLI has `discover` but not `analyze`. | `src/akwb/cli.py` has no `analyze` command; `Container` has no extraction/knowledge engine. |
| 2 | **At least one source-code parser** | Software projects are mostly code. Markdown alone cannot extract components, APIs, imports, or dependencies. | No Python/Node/Java parser exists; roadmap promised Phase 2 parsers. |
| 3 | **Relationship extraction** | The graph is only useful if edges connect units. Currently no `RelationshipBuilder` extracts imports, calls, or doc-to-code links. | `docs/08_KNOWLEDGE_ENGINE.md` describes it; `src/akwb/extraction/` has no relationship builder. |
| 4 | **Graph persistence and workspace materialization** | The graph engine raises `RuntimeError` when saving without a backend. Workspace bootstrap only writes `workspace.json`. | `src/akwb/graph/engine.py` `save()` requires `GraphStorage`; `.akwb/` only creates `logs`, `cache`, `staging`. |
| 5 | **Extraction pipeline integration in Container/CLI** | `ExtractionPipeline` and `GraphEngine` exist as libraries but are not invoked by the product. | `src/akwb/container.py` does not instantiate either. |
| 6 | **Plugin loading in CLI flow** | `Container.load_plugins()` exists but is not called by `discover` or future `analyze`. | `src/akwb/cli.py` `discover` never calls `container.load_plugins()`. |
| 7 | **Export API commands** | Downstream products need `akwb report`/`export` to produce JSONL/DOT/Cypher artifacts. | CLI has no `report` or `export` command. |

**Non-required gaps (nice-to-have, defer):** AI summarization, embeddings, vector
indexes, marketplace, IDE UI, web dashboard, real-time watch mode.

## 6. Simplification Review

| Abstraction / Layer | Current State | Simplification Recommendation | Impact |
|---|---|---|---|
| **AI Engine** | Documented but not implemented; overlaps with AI Context Builder. | **Remove from MVP.** AKWB exports graph data; downstream products build context. | High. Avoids duplicating AI Context Builder and reduces dependencies. |
| **Workspace Engine vs. Storage** | Two separate concepts (`workspace/bootstrap.py`, `storage/local.py`) that both manage `.akwb/`. | Keep separation but merge bootstrap into storage; bootstrap should only create directories and write `workspace.json`. | Medium. Reduces confusion. |
| **Unit of Work** | Defined in `storage/unit_of_work.py` but not used by CLI or engines. | Either implement it for `analyze` or remove until transactional workspace writes are needed. | Low-Medium. Avoids dead code. |
| **InMemoryEventBus** | Exists and publishes events, but no subscriber orchestrates work. | Keep for decoupling, but do not expand. It is acceptable for MVP. | Low. |
| **Multiple text segmenters** | `HeadingSegmenter`, `ParagraphSegmenter`, `CodeSegmenter`, `TableSegmenter` are regex-based and overlap with AST parser output. | Keep as fallbacks for plain text, but prefer AST parsers. Eventually consolidate behind `AdaptiveSegmenter`. | Low. |
| **SemanticSegmenter** | Sentence-level segmentation. | **Defer.** Not needed until downstream products request it. | Low. |
| **GraphStorage port with no backend** | `GraphEngine.save()` fails without a plugin. | Implement a `LocalGraphStorage` backend that writes JSONL/DOT/Cypher to `.akwb/graph/`. | High. Closes gap 4. |
| **KnowledgeVersion / Lifecycle** | Implemented in framework. | Keep; they are cheap and support downstream traceability. | Low. |
| **Plugin Marketplace** | Documented future. | **Remove from MVP roadmap.** Keep local plugin loading only. | High. Reduces scope and security surface. |
| **Seven first-class engines** | Architecture lists Discovery, Knowledge, Workspace, AI, Graph, Memory, Incremental. | Collapse to **Discovery, Extraction/Knowledge, Graph, Workspace** for MVP. Remove AI and Memory as separate engines. | High. Focuses the architecture. |

## 7. Minimum Viable Engine

The smallest reusable AKWB engine must:

1. Run `akwb analyze <path>` end-to-end.
2. Discover files and build a `SourceCatalog`.
3. Parse at least Markdown and one source-code language (Python).
4. Extract `KnowledgeObject`s and `KnowledgeRelationship`s.
5. Build and validate a `KnowledgeGraph`.
6. Persist the graph and catalog to `.akwb/`.
7. Export graph data as JSONL, DOT, and Cypher.
8. Support local plugins for parsers and extractors.
9. Provide `init`, `doctor`, `analyze`, `report`/`export`, `clean`, and `version` CLI commands.

### Core Modules

- `akwb.cli` — `init`, `doctor`, `analyze`, `report`, `export`, `clean`, `version`.
- `akwb.config` — configuration loading and validation.
- `akwb.container` — wire storage, discovery, extraction, graph, and workspace.
- `akwb.discovery` — scan, classify, fingerprint, incremental diff.
- `akwb.storage` — local workspace I/O and atomic writes.
- `akwb.workspace` — workspace bootstrap and manifest.
- `akwb.extraction` — parser framework, Markdown reader/segmenter, Python parser, rule-based extractor, candidate builder.
- `akwb.knowledge` — domain model, framework, validation, serialization.
- `akwb.graph` — graph model, index, query, traversal, validation, statistics, persistence.
- `akwb.plugins` — local plugin loader and registry.
- `akwb.types`, `akwb.events`, `akwb.observability` — shared primitives.

### Required Plugins

- Markdown parser/reader/segmenter (built-in).
- Python AST parser/reader/segmenter (built-in or plugin).
- Rule-based extractor (built-in).
- Default knowledge object builder (built-in).
- Local storage backend (built-in).

### Required APIs / Exports

- `ExtractionPipeline.extract(artifact, content)` → `ExtractionResult`.
- `GraphEngine.build(catalog)` → `KnowledgeGraph`.
- `GraphEngine.query(...)` / `traverse(...)` / `validate(...)` / `statistics(...)`.
- CLI `akwb analyze` producing `.akwb/`.
- `.akwb/index/source_catalog.jsonl`.
- `.akwb/knowledge/graph_nodes.jsonl` and `graph_edges.jsonl`.
- `.akwb/graph/graph.jsonl`, `graph.dot`, `graph.cypher`.
- `.akwb/reports/summary.md` and `summary.json`.

### Not in MVP

- AI summarization, chunking, embeddings, RAG.
- Plugin marketplace.
- IDE UI, web dashboard, chat.
- Publishing platform.
- Real-time watch mode.
- Multi-project federation.
- Cloud/SaaS operations.

## 8. Final Roadmap Recommendation

The current roadmap is directionally correct but includes consumer-facing
sprints (AI Engine, Reports-as-product, Marketplace) that should be deferred or
removed.

### Recommended Roadmap

| Phase | Sprints | Goal |
|---|---|---|
| **Phase 1: Core Engine** | Sprints 1–6 (complete) + Sprint 7 | Close end-to-end `analyze`, add Python parser, persist graph, export artifacts. |
| **Phase 2: Relationship & Depth** | Sprints 8–9 | Import/call/reference resolution, dependency graph, cross-file traceability. |
| **Phase 3: Parsers & Ecosystem** | Sprints 10–11 | Node.js, Java, Go, Rust, PHP parsers; plugin SDK. |
| **Phase 4: Hardening & Release** | Sprints 12–13 | Performance, security, packaging, CLI polish, public beta. |
| **Phase 5: Future** | Post-beta | Marketplace, AI context integration (downstream), federation, cloud. |

### Sprint Re-Definition

| Sprint | Recommended Scope | Status |
|---|---|---|
| **Sprint 7: End-to-End Engine & Python Parser** | Add `akwb analyze` command, integrate `ExtractionPipeline` and `GraphEngine`, implement `LocalGraphStorage`, add a Python AST parser, produce `.akwb/` artifacts. | New |
| **Sprint 8: Relationship Extraction** | Implement `RelationshipBuilder` port; extract imports, calls, inheritance, doc-to-code links; build dependency graph. | New |
| **Sprint 9: Traceability & Coverage** | Link tests to code, docs to code, config to features; compute coverage metrics. | New |
| **Sprint 10: Multi-Language Parsers** | Node.js parser; framework for Java/Go/Rust/PHP plugins. | Replaces AI Engine sprint |
| **Sprint 11: Plugin SDK & DX** | Reference plugin, contract tests, `akwb plugin` commands, documentation. | Replaces Marketplace sprint |
| **Sprint 12: Performance & Security** | Benchmarking, secret scanning, sandboxing, packaging, SBOM. | Replaces Phase 3 Reports |
| **Sprint 13: Beta Release** | CI/CD, signed releases, migration guide, public beta. | New |

### Removed / Deferred

- **AI Engine sprint** — Removed from core. AI context is a downstream concern.
- **Report/Dashboard sprint** — Replaced with minimal export artifacts.
- **Marketplace sprint** — Deferred to post-beta ecosystem work.
- **Workspace visualization** — Out of scope; belongs to StayOS/dashboard products.

## 9. GO / NO-GO Decision

**Recommended decision: OPTION B — Modify the roadmap.**

### Justification

The product vision is still valid. The engine architecture is sound. The
completed sprints produced high-quality, reusable components. However, the
roadmap must be tightened to avoid scope creep into downstream product territory
and to close the critical end-to-end gap.

### Evidence

- The `akwb analyze` command is missing, so no end-to-end value is delivered yet.
- The graph engine is not persisted to `.akwb/`.
- No source-code parser exists beyond Markdown.
- No relationship extraction exists.
- The planned AI Engine and Marketplace overlap with downstream products and
  would duplicate effort.

### Conditions for proceeding

1. Approve the boundary definitions in this review.
2. Remove AI Engine and Marketplace from MVP.
3. Prioritize Sprint 7 (end-to-end `analyze` + Python parser + graph persistence).
4. Add relationship extraction as a required follow-up.
5. Do not begin any new feature implementation until this review is approved.

### If this review is not approved

Implement the following fallback:

- Freeze all new code.
- Re-scope AKWB as a narrower "Markdown Knowledge Extractor" if the engine
  boundary cannot be held.
- Otherwise, perform a full architecture reset to redefine product boundaries.

---

## Output Documents

- `docs/PRODUCT_SCOPE.md` — concise purpose and boundary statements.
- `docs/MVP_DEFINITION.md` — smallest complete reusable engine.
- `docs/ROADMAP_RECOMMENDATION.md` — revised sprint sequence.
- `docs/EXECUTIVE_SUMMARY.md` — leadership summary and decision.
