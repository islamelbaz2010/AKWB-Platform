# AKWB MVP Readiness Audit

**Status:** Sprint 7 Readiness Review — Implementation Freeze  
**Goal:** Determine exactly what prevents AKWB from becoming a usable
Enterprise Knowledge Compiler today.  
**Constraint:** No architecture changes. No code changes. Evidence only.

---

## Section 1 — Current Product

AKWB, as it exists today, is a **well-structured but incomplete engine**. The
individual components are built and tested as libraries, but they are not wired
into an end-to-end product.

### What currently works

| Capability | Status | Evidence |
|---|---|---|
| Project discovery | Works | `src/akwb/discovery/engine.py`, `tests/integration/test_discovery_cli.py` |
| File classification | Works | `src/akwb/discovery/classifier.py` |
| Fingerprinting and incremental diff | Works | `src/akwb/discovery/fingerprint.py`, `src/akwb/discovery/incremental.py` |
| Knowledge Object Framework | Works | `src/akwb/knowledge/`, `tests/unit/knowledge/` |
| Extraction Pipeline | Works as library | `src/akwb/extraction/pipeline.py`, `tests/unit/extraction/test_pipeline.py` |
| Markdown AST Parser | Works | `src/akwb/extraction/markdown.py`, `tests/integration/extraction/test_markdown_files.py` |
| Knowledge Graph Engine | Works as library | `src/akwb/graph/engine.py`, `tests/unit/graph/test_engine.py` |
| Plugin loader and registry | Works | `src/akwb/plugins/loader.py`, `src/akwb/plugins/registry.py` |
| Local storage backend | Works | `src/akwb/storage/local.py` |
| Workspace bootstrap | Works | `src/akwb/workspace/bootstrap.py` |
| Configuration loading | Works | `src/akwb/config.py` |
| `akwb version`, `init`, `doctor`, `discover` | Implemented | `src/akwb/cli.py` |
| Unit and integration tests | All pass | `python3 -m pytest -q` exits 0 |

### What does NOT work as a product

- No `akwb analyze` command.
- No orchestration that links discovery → extraction → graph → workspace.
- No graph persistence to `.akwb/`.
- No `report` or `export` commands.
- No relationship extraction for code imports or file dependencies.
- No Python source-code parser; code files fall back to plain-text reading.
- Container does not instantiate `ExtractionPipeline` or `GraphEngine`.
- CLI does not load plugins before running discovery.

---

## Section 2 — End-to-End Flow

| Stage | Implemented? | Integrated? | Callable? | Tested? | Production Ready? |
|---|---|---|---|---|---|
| **Project input** | Yes (CLI `--project-root`) | Yes | `akwb init / discover` | Yes | No (only `init`/`discover`) |
| **Discovery** | Yes | Partially | `Container.discovery_engine` | Yes | No (not called by `analyze` because no `analyze`) |
| **Parser** | Yes (Markdown, text, structured readers) | No | Library only | Yes | No (not wired to CLI) |
| **Extraction** | Yes | No | `ExtractionPipeline.extract()` | Yes | No (not wired to CLI) |
| **Knowledge Objects** | Yes | No | `KnowledgeFramework` | Yes | No (no catalog assembly from extraction) |
| **Knowledge Graph** | Yes | No | `GraphEngine.build()` | Yes | No (not called from CLI; no persistence) |
| **Workspace** | Partial | Partial | `WorkspaceBootstrap.init()` | Yes | No (only manifest created) |
| **Export** | Partial (serializers exist) | No | `KnowledgeFramework.serialize_catalog()` | Yes | No (no export CLI or pipeline) |

### Flow trace

1. `akwb analyze myproject` → **missing**. The command is not registered.
2. Discovery (`akwb discover myproject`) → works, writes `artifacts.json`.
3. Parser/Extraction → only callable programmatically; no path reads file bytes and runs pipeline.
4. `KnowledgeCatalog` assembly → missing. `ExtractionPipeline` returns a list of `KnowledgeObject`s, but no orchestrator aggregates them into a `KnowledgeCatalog` with types and relationships.
5. Graph build → `GraphEngine.build(catalog)` exists but is not invoked.
6. Graph persistence → `GraphEngine.save()` raises `RuntimeError` because no `GraphStorage` backend exists.
7. Workspace artifacts → only `workspace.json`, `logs/`, `cache/`, `staging/` created.
8. Export → no CLI command.

---

## Section 3 — Vertical Slice

### Question

Can a user install AKWB today and execute `akwb analyze myproject` successfully?

**Answer: No.**

### Blockers (ranked by severity)

| # | Blocker | Severity | Why It Blocks |
|---|---|---|---|
| 1 | **`akwb analyze` command does not exist** | Critical | The primary user action is missing. `grep` for `analyze` in `src/akwb/*.py` returns no results. |
| 2 | **No orchestration between engines** | Critical | Discovery, extraction, and graph are standalone libraries with no caller. `Container` only wires `DiscoveryEngine`. |
| 3 | **No graph persistence** | Critical | `GraphEngine.save()` raises `RuntimeError` because no `GraphStorage` implementation is registered. The workspace would contain no graph. |
| 4 | **No `KnowledgeCatalog` assembly from extraction results** | High | `ExtractionPipeline.extract()` returns a list of objects. No code aggregates them into a catalog or adds relationships. |
| 5 | **No relationship extraction** | High | The graph will be disconnected nodes. No `RelationshipBuilder` exists. Code imports, file containment, and doc-to-code links are absent. |
| 6 | **No `report` / `export` commands** | Medium | Downstream products have no documented way to retrieve artifacts from `.akwb/`. |
| 7 | **No source-code parser** | Medium | `.py` files are read as plain text and produce low-value keyword matches. Real code structure is not extracted. |
| 8 | **CLI does not load plugins** | Medium | `Container.load_plugins()` exists but is never called, so plugin readers/extractors cannot participate. |
| 9 | **`UnitOfWork` is constructed but not used** | Low | Transaction staging is dead code until `analyze` commits artifacts. |

---

## Section 4 — Missing Links

Only integration gaps. No future enhancements.

1. **CLI → Container wiring**
   - `cli.py` has no `analyze` command.
   - `cli.py` does not call `container.load_plugins()`.

2. **Container → ExtractionPipeline and GraphEngine**
   - `Container.__init__` creates `DiscoveryEngine` only.
   - `ExtractionPipeline` and `GraphEngine` must be instantiated and configured with plugins.

3. **Discovery → Extraction**
   - `DiscoveryEngine.discover()` returns an `ArtifactRegistry`.
   - No code iterates over artifacts, reads their bytes, and runs `ExtractionPipeline.extract()`.

4. **Extraction → KnowledgeCatalog**
   - `ExtractionPipeline.extract()` returns `ExtractionResult` with a list of `KnowledgeObject`s.
   - No code aggregates results into a `KnowledgeCatalog` or adds built-in types.

5. **KnowledgeCatalog → Graph**
   - `GraphEngine.build(catalog)` exists but is not invoked.

6. **Graph → Workspace**
   - `GraphEngine.save()` requires a `GraphStorage` backend.
   - No `LocalGraphStorage` implementation exists.
   - No code writes `graph_nodes.jsonl`, `graph_edges.jsonl`, `graph.dot`, `graph.cypher`.

7. **CLI → Reports / Exports**
   - No `akwb report` or `akwb export` command.

8. **Plugin loading in the CLI flow**
   - `Container.load_plugins()` is not invoked by `discover`, `init`, or any future `analyze`.

9. **Lifecycle / UnitOfWork**
   - `UnitOfWork` stages artifacts but no command commits them.

10. **Source catalog persistence location**
    - `artifacts.json` is written at the storage root, not under `index/source_catalog.jsonl` as documented in `docs/15_STORAGE_MODEL.md`.

---

## Section 5 — False Gaps

These items appear in the original roadmap but are **not required for MVP**.

| Item | Why Deferred |
|---|---|
| AI Engine (summarization, chunking, embeddings, RAG) | Constitution forbids AI runtime inside AKWB. Downstream products own AI. |
| Plugin marketplace | Ecosystem feature; local plugin loading is sufficient for MVP. |
| Dashboard / Web UI | Out of scope; downstream products render `.akwb/` artifacts. |
| Business dashboards, CRM, workflow automation | Business logic belongs downstream. |
| Node.js / Java / Go / Rust / PHP parsers | Required for scale and language coverage, but not for first usable MVP. |
| Cloud operations / multi-tenancy | Hosting is a downstream platform concern. |
| Real-time watch mode | Nice-to-have; not required for baseline `akwb analyze`. |
| Advanced relationship resolution (rename detection, dynamic imports) | Important but not blocking first graph export. |

The engine can be usable with Markdown, a basic Python reader, and end-to-end
wiring. Additional languages and AI features are growth work, not MVP gates.

---

## Section 6 — Product Completeness Score

| Dimension | Score | Justification |
|---|---|---|
| **Architecture** | 8/10 | Clean, bounded, plugin-based. Only gap: graph persistence port lacks a built-in backend. |
| **Implementation** | 6/10 | All core libraries exist and pass tests. Missing: `analyze` command, orchestration, graph storage, code parser. |
| **Integration** | 2/10 | Only `discover` is wired end-to-end. Extraction and graph are libraries with no CLI integration. |
| **Usability** | 1/10 | A user cannot run the primary command. `init` and `discover` are internal preliminaries. |
| **Developer Experience** | 5/10 | Good tests, docs, types. No runnable `analyze` example. No `report`/`export` for consumers. |
| **CLI** | 2/10 | Only `version`, `init`, `doctor`, `discover` exist. Primary `analyze` and secondary `report`/`export` missing. |
| **Workspace** | 4/10 | `workspace.json` is created. No graph, catalog, or report artifacts are materialized. |
| **Plugin System** | 7/10 | Loader and registry work. Plugin ports defined. Not invoked by CLI; no `GraphStorage` implementation. |
| **Documentation** | 9/10 | Constitution, architecture, roadmap, and sprint reports are comprehensive. MVP acceptance test missing until this audit. |
| **Testing** | 8/10 | Unit and integration tests pass. No end-to-end `analyze` test. |
| **Overall MVP Readiness** | **3/10** | Components are solid, but they are not a product. The remaining work is integration and CLI wiring, not architecture. |

---

## Section 7 — Shortest Path to MVP

These are the **minimum** tasks required for AKWB to become usable. Everything
else is excluded.

1. Implement `akwb analyze <path>` CLI command.
2. Wire `ExtractionPipeline` and `GraphEngine` into `Container`.
3. Load plugins at the start of `analyze`.
4. Iterate over the `ArtifactRegistry`, read each file, and run extraction.
5. Aggregate `ExtractionResult`s into a `KnowledgeCatalog`.
6. Build a `KnowledgeGraph` from the catalog.
7. Validate the graph.
8. Implement and register a `LocalGraphStorage` backend.
9. Persist graph artifacts to `.akwb/graph/`.
10. Persist source catalog to `.akwb/index/source_catalog.jsonl`.
11. Persist knowledge catalog/objects to `.akwb/knowledge/`.
12. Add `akwb report` and `akwb export` commands.
13. Add a basic Python source-code parser (or at minimum a code-aware
    reader/segmenter) so `.py` files produce meaningful components.
14. Add an MVP acceptance test that runs `akwb analyze` on a sample project.

Without these, AKWB cannot be used as a knowledge compiler. Any feature not on
this list is deferred.

---

## Section 8 — Sprint 7 Task Breakdown

Sprint 7 is an integration sprint. It does not add new engines or new
abstractions. It wires existing engines into a product.

### Task 1 — Register `akwb analyze` CLI command
- Add `analyze` command to `src/akwb/cli.py`.
- Support `--force`, `--depth`, `--json`.
- Validate project root and exit codes.

### Task 2 — Wire `ExtractionPipeline` and `GraphEngine` into `Container`
- Instantiate `ExtractionPipeline` and `GraphEngine` in `Container.__init__`.
- Share `KnowledgeFramework` and `Observability` between them.
- Ensure `Container.load_plugins()` extends both pipeline and graph.

### Task 3 — Call `load_plugins()` in CLI flow
- `analyze` and `discover` must invoke `container.load_plugins()` before
  processing.

### Task 4 — Implement `analyze` orchestrator
- For each `ArtifactEntry` in the registry:
  - Read file bytes from disk.
  - Call `ExtractionPipeline.extract()`.
  - Collect objects and diagnostics.
- Skip binary/unreadable files with a diagnostic.

### Task 5 — Assemble `KnowledgeCatalog`
- Create `KnowledgeCatalog` from `KnowledgeFramework`.
- Add all extracted objects.
- Add synthetic `contains` relationships from file → object.

### Task 6 — Build and validate `KnowledgeGraph`
- `GraphEngine.build(catalog)`.
- `GraphEngine.validate(graph)`.
- `GraphEngine.statistics(graph)` for diagnostics.

### Task 7 — Implement `LocalGraphStorage`
- Implement `GraphStorage` port.
- Save/load graph to/from `.akwb/graph/` as JSONL/DOT/Cypher.
- Register it as a built-in plugin.

### Task 8 — Persist workspace artifacts
- `artifacts.json` or `index/source_catalog.jsonl`.
- `knowledge/catalog.jsonl` or `knowledge/graph_nodes.jsonl` and
  `knowledge/graph_edges.jsonl`.
- `graph/graph.jsonl`, `graph/graph.dot`, `graph/graph.cypher`.
- `reports/summary.md`, `reports/summary.json`.
- Update `workspace.json` manifest.

### Task 9 — Add `akwb report` and `akwb export`
- `report summary|structure|graph` reads workspace and prints/renders.
- `export jsonl|dot|cypher` writes to `.akwb/graph/` or stdout.

### Task 10 — Basic Python source-code parser
- Add `PythonReader`/`PythonSegmenter`/`PythonExtractor` (or extend
  `RuleBasedExtractor`) to produce `component`/`function` objects from `.py`
  files.
- Start with `ast` module; no type inference.

### Task 11 — End-to-end integration tests
- CLI test running `akwb analyze` on a fixture project.
- Assert workspace artifacts exist and are non-empty.
- Assert graph has at least one edge.

### Task 12 — MVP acceptance test
- Define and commit sample project fixture.
- Run `akwb init`, `akwb analyze`, verify outputs.

---

## Section 9 — MVP Acceptance Test

### Scenario

A fresh AKWB installation is used on a sample project.

### Sample project structure

```
sample_project/
  README.md
  docs/
    architecture.md
  src/
    app.py
  tests/
    test_app.py
```

`README.md`:

```markdown
# Sample Project

This project demonstrates AKWB.

## Decision

We will use PostgreSQL for persistence.
```

`src/app.py`:

```python
from . import config

def connect():
    return config.get_dsn()
```

### Steps

1. `pip install -e .`
2. `akwb init sample_project`
3. `akwb analyze sample_project`

### Expected CLI output (non-JSON)

```
Analyzed 4 artifacts
Generated .akwb/workspace
Knowledge objects: 5
Knowledge edges: 2
```

### Expected exit code

`0` on success, non-zero on failure.

### Expected `.akwb` structure

```
.akwb/
  workspace.json
  index/
    source_catalog.jsonl
  knowledge/
    catalog.jsonl
    graph_nodes.jsonl
    graph_edges.jsonl
  graph/
    graph.jsonl
    graph.dot
    graph.cypher
  reports/
    summary.md
    summary.json
  logs/
    analysis.log
```

### Expected graph contents

- At least one `document` object from `README.md`.
- At least one `decision` object from the heading "Decision".
- At least one `component` or `function` object from `app.py`.
- A `contains` edge from `README.md` to the decision object.
- A `contains` edge from `src/app.py` to the function/component object.
- Optionally a `depends_on` edge from `app.py` to `config`.

### Expected `reports/summary.md`

```markdown
# AKWB Analysis Summary

- Artifacts analyzed: 4
- Knowledge objects: 5
- Knowledge relationships: 2
- Graph density: ...
```

---

## Section 10 — GO / NO-GO Decision

### Recommendation: **GO**

AKWB is ready to enter **Sprint 7** as a pure integration sprint.

### Justification

- The architecture is sound and approved.
- The Constitution and product boundaries are ratified.
- All required engine components exist and pass tests as libraries.
- No architecture changes are required.
- The remaining work is wiring, persistence, and CLI completion.
- The blockers are known, ranked, and bounded.

### Conditions

- Do not expand scope into AI, marketplace, multi-language parsers, or UI during
  Sprint 7.
- Every Sprint 7 task must directly close an MVP blocker listed in Section 4.
- The MVP acceptance test in Section 9 must pass before declaring Sprint 7
  complete.

### If conditions are not met

If any task requires a new engine, a new abstraction, or a change to the
Constitution, escalate to Architecture Review before proceeding.
