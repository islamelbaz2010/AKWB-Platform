# Executive Summary — AKWB Product Boundary Review

## Review Purpose

This review determines whether the AKWB project is still building the intended
product: a reusable **Enterprise Knowledge Extraction Engine**. It is not a
code review or an architecture review. It evaluates product scope, boundaries,
overlap with downstream products, and roadmap realism.

## Bottom Line

**AKWB is building the right product, but the roadmap must be modified to avoid
scope creep and to close a critical end-to-end gap.**

The engine components completed so far are sound, well-tested, and properly
scoped. However, they are not yet assembled into a working `akwb analyze`
command, and the current roadmap includes consumer-facing features that belong
in downstream products.

## What AKWB Is and Is Not

**AKWB is** an engine that:

- Discovers project files.
- Parses source files into normalized content.
- Extracts typed `KnowledgeObject`s.
- Builds a validated `KnowledgeGraph`.
- Persists the graph to a project-owned `.akwb/` workspace.
- Exports graph data as JSONL, JSON, YAML, DOT, and Cypher.
- Supports local plugins for parsers, extractors, and graph backends.

**AKWB is not** an end-user platform. It does not provide:

- AI chat, agent runtime, or prompt management.
- Workspace dashboards, publishing platforms, or business analytics.
- Workflow automation, CRM integrations, or memory UIs.
- IDE UI panels, web dashboards, or marketplaces.

Downstream products such as **Eunoia AI OS**, **EPOS**, **AI Context Builder**,
and **StayOS** are expected to consume `.akwb/` artifacts and build their own
experiences on top.

## Key Findings

### 1. The vision is intact

The original product vision (local-first, project-owned `.akwb/` workspace,
CLI-driven, reusable engine) remains valid. The architecture and domain model
support it.

### 2. Individual sprints are high quality

Sprints 1–6 produced working, well-typed, well-tested libraries:

- Discovery engine can scan and fingerprint projects.
- Knowledge Object Framework provides a strong canonical model.
- Extraction Pipeline has a clean plugin architecture.
- Knowledge Graph Engine supports query, traversal, validation, and statistics.
- Markdown AST Parser is a good reference parser.

### 3. The components are not yet wired together

The CLI currently only supports `version`, `init`, `doctor`, and `discover`.
There is no `akwb analyze` command. The `Container` does not instantiate the
`ExtractionPipeline` or `GraphEngine`. `ExtractionPipeline` works only as a
library. This is the most important gap.

### 4. A code parser is missing

AKWB targets software projects, but it only has a Markdown parser. A Python AST
parser is the minimum next parser required for the engine to be useful.

### 5. Relationship extraction is missing

The Knowledge Graph Engine can store and query edges, but no extractor produces
`KnowledgeRelationship`s (imports, calls, contains, documents). The graph is
currently just isolated nodes.

### 6. Graph persistence is missing

`GraphEngine.save()` raises `RuntimeError` unless a `GraphStorage` plugin is
configured, and no local backend is implemented. The workspace bootstrap only
writes `workspace.json` and empty directories.

### 7. Scope creep threatens the roadmap

The planned AI Engine (summarization, chunking, embeddings, RAG) duplicates
responsibilities that belong to **AI Context Builder** and **Eunoia AI OS**.
The planned plugin marketplace and dashboard features are ecosystem and
consumer concerns, not engine requirements.

## Overlap Assessment

| Downstream Product | Overlap Risk | AKWB Boundary |
|---|---|---|
| Eunoia AI OS | Memory, context, chat, agent runtime | Export `KnowledgeGraph`; do not build memory or agent runtime. |
| EPOS | Publishing, themed reports | Export raw reports; EPOS publishes them. |
| AI Context Builder | Embeddings, chunking, prompt assembly | Export structured graph data; do not build embeddings or prompt UI. |
| StayOS | Dashboards, workspace overview | Export workspace artifacts; StayOS renders them. |

## Gap Analysis

Only gaps that block a production-ready engine:

1. **End-to-end `akwb analyze` command.**
2. **Source-code parser (Python minimum).**
3. **Relationship extraction (imports, calls, references).**
4. **Graph persistence and workspace materialization.**
5. **Extraction/Graph integration in `Container` and CLI.**
6. **Plugin loading during CLI flow.**
7. **Export commands (`report`, `export`).**

Nice-to-have features (AI summarization, embeddings, marketplace, dashboards)
are not required and should be deferred.

## Simplification Recommendations

- **Remove the AI Engine from core.** Downstream products own AI context.
- **Remove the Marketplace from MVP.** Defer until after beta.
- **Merge Reports into Export API.** Produce raw artifacts, not a report product.
- **Implement `LocalGraphStorage`.** Close the graph persistence gap.
- **Use the event bus and unit-of-work only where they add real value.** Do not
  expand them prematurely.
- **Keep text regex segmenters as fallbacks** but prefer AST parsers for known
  languages.

## Minimum Viable Engine

The smallest complete AKWB must:

- Run `akwb analyze <path>` end-to-end.
- Discover files and produce a `SourceCatalog`.
- Parse Markdown and Python files.
- Extract `KnowledgeObject`s and `KnowledgeRelationship`s.
- Build and validate a `KnowledgeGraph`.
- Persist the graph and catalog to `.akwb/`.
- Export JSONL, DOT, and Cypher.
- Support local plugins.
- Provide `init`, `doctor`, `analyze`, `report`/`export`, `clean`, and `version`.

See `docs/MVP_DEFINITION.md` for full details.

## Recommended Roadmap

| Phase | Sprints | Focus |
|---|---|---|
| Phase 1 | Sprints 1–6 (done) | Foundation, Discovery, Knowledge Framework, Extraction Pipeline, Graph Engine, Markdown Parser. |
| Phase 2 | Sprints 7–10 | End-to-end `analyze`, Python parser, relationship extraction, graph persistence/exports. |
| Phase 3 | Sprints 11–13 | Multi-language parsers (Node.js, Java/Go/Rust/PHP), plugin SDK. |
| Phase 4 | Sprints 14–16 | Performance, security, packaging, beta release. |
| Future | Post-beta | Marketplace, optional AI context exports, federation, dashboard integrations. |

## GO / NO-GO Decision

**Recommended: OPTION B — Modify the roadmap.**

The product boundary is correct. The engine architecture is sound. The
completed sprints are valuable. The roadmap must be tightened to:

1. Remove consumer-facing AI and Marketplace sprints from MVP.
2. Prioritize end-to-end `akwb analyze` and a Python parser.
3. Add relationship extraction and graph persistence.
4. Maintain the engine/downstream boundary.

## Next Steps

If approved:

1. Freeze all feature implementation pending this review.
2. Approve `PRODUCT_SCOPE.md`, `MVP_DEFINITION.md`, and
   `ROADMAP_RECOMMENDATION.md`.
3. Begin Sprint 7: end-to-end `akwb analyze` integration.
4. Do not begin AI Engine, Marketplace, Dashboard, or Chat features until the
   engine is reusable end-to-end.

If not approved:

- Option C: Freeze implementation and redefine product boundaries, or
- Narrow scope to a Markdown-only knowledge extractor.

## Output Documents

- `docs/PRODUCT_SCOPE.md` — What AKWB is and is not.
- `docs/PRODUCT_BOUNDARY_REVIEW.md` — Full Section 1–9 review.
- `docs/MVP_DEFINITION.md` — Smallest complete reusable engine.
- `docs/ROADMAP_RECOMMENDATION.md` — Revised sprint sequence.
- `docs/EXECUTIVE_SUMMARY.md` — This document.
