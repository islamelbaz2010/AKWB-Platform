# AKWB MVP Blockers

This document lists only the blockers preventing AKWB from becoming a usable
Enterprise Knowledge Compiler. It is derived from `docs/MVP_READINESS_AUDIT.md`
and `docs/VERTICAL_SLICE_ANALYSIS.md`.

## Critical Blockers

### 1. Missing `akwb analyze` Command

- **Impact:** The primary user action does not exist. AKWB cannot be used.
- **Evidence:** `src/akwb/cli.py` registers `version`, `init`, `doctor`, and
  `discover` only. `grep -r "analyze" src/akwb/*.py` returns nothing.
- **Required Fix:** Add `akwb analyze <path>` to `cli.py` with `--force`,
  `--depth`, and `--json` flags.

### 2. Missing Orchestration in `Container`

- **Impact:** `ExtractionPipeline` and `GraphEngine` exist as libraries but are
  not available to the CLI.
- **Evidence:** `src/akwb/container.py` instantiates only `DiscoveryEngine`.
  `ExtractionPipeline` and `GraphEngine` are not created.
- **Required Fix:** Wire `ExtractionPipeline` and `GraphEngine` into
  `Container` and share `KnowledgeFramework` and `Observability`.

### 3. Missing Graph Persistence

- **Impact:** `GraphEngine` cannot persist a `KnowledgeGraph` to the workspace.
- **Evidence:** `src/akwb/graph/engine.py` `save()` raises
  `RuntimeError("No graph storage backend configured")`. `GraphStorage` is an
  abstract port in `src/akwb/graph/plugins.py` with no implementation.
- **Required Fix:** Implement `LocalGraphStorage` and register it as a built-in
  plugin. Write graph artifacts under `.akwb/graph/`.

## High-Severity Blockers

### 4. Missing `KnowledgeCatalog` Assembly

- **Impact:** Extracted objects are isolated; there is no aggregate for the graph
  engine.
- **Evidence:** `ExtractionPipeline.extract()` returns `ExtractionResult` with a
  list of `KnowledgeObject`s. No code converts the list into a
  `KnowledgeCatalog`.
- **Required Fix:** Add an `AnalyzeEngine` or `KnowledgeEngine` orchestrator that
  creates a `KnowledgeCatalog` from extraction results and adds synthetic
  `contains` relationships.

### 5. Missing Relationship Extraction

- **Impact:** The knowledge graph is a set of disconnected nodes.
- **Evidence:** No `RelationshipBuilder` port or implementation exists in the
  source. `grep -r "RelationshipBuilder" src/akwb` returns nothing.
- **Required Fix:** Define and implement `RelationshipBuilder` port. For MVP,
  produce `contains` relationships from file → object and `depends_on` edges
  from Python imports.

## Medium-Severity Blockers

### 6. Missing `report` and `export` Commands

- **Impact:** Downstream products cannot retrieve artifacts through the CLI.
- **Evidence:** `src/akwb/cli.py` has no `report` or `export` commands.
- **Required Fix:** Add `akwb report <name>` and `akwb export <format>` that read
  `.akwb/` and produce outputs.

### 7. Plugin Loading Not Called in CLI Flow

- **Impact:** Plugin readers/extractors are never loaded.
- **Evidence:** `Container.load_plugins()` exists but is not invoked by `cli.py`.
- **Required Fix:** Call `container.load_plugins()` before discovery and
  extraction in `analyze` and `discover`.

### 8. No Source-Code Parser

- **Impact:** `.py` files are read as plain text and produce low-value keyword
  matches. Real software projects cannot be analyzed.
- **Evidence:** `TextReader` handles all `text/*` MIME types, including
  `text/x-python` if the MIME is set. `RuleBasedExtractor` only matches keywords
  in text segments. There is no Python AST reader/segmenter/extractor.
- **Required Fix:** Add a minimal Python source-code parser that emits
  `component` and `function` objects with source spans.

## Low-Severity Blockers

### 9. Unused `UnitOfWork`

- **Impact:** Transaction staging is dead code; workspace commits may not be
  atomic.
- **Evidence:** `src/akwb/storage/unit_of_work.py` is constructed but never
  committed.
- **Required Fix:** Use `UnitOfWork` during `analyze` to stage artifacts and
  commit the manifest atomically.

## Non-Blockers (Deferred)

These are intentionally not blockers because they are out of scope or
post-MVP:

- AI Engine, embeddings, RAG.
- Plugin marketplace.
- Dashboard, web UI, IDE UI.
- Node.js, Java, Go, Rust, PHP parsers.
- Cloud, multi-tenant operations, federation.
- Advanced relationship resolution (rename detection, dynamic call graphs).

## Summary

AKWB has **three critical**, **two high**, **three medium**, and **one low**
blocker before MVP. The critical blockers are all integration and persistence
problems, not missing engine components. The engine libraries are ready; the
product wiring is not.
