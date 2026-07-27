# Sprint 7 Execution Plan

**Sprint Goal:** Make AKWB a usable Enterprise Knowledge Compiler by wiring
existing engines into a single `akwb analyze` command and producing a
persisted, exportable `.akwb/` workspace.

**Sprint Type:** Integration only. No new engines, no new abstractions, no
architecture changes. All work must comply with the AKWB Constitution.

## Constraints

- Do not implement AI, marketplace, dashboard, or UI features.
- Do not add Node, Java, Go, Rust, or PHP parsers yet.
- Do not modify the existing plugin port contracts without Architecture Review.
- Every task must be independently reviewable.
- Each task must have unit or integration tests.

---

## Task 1: Register `akwb analyze` CLI Command

**Owner:** CLI  
**Priority:** Critical

1. Add `analyze` command to `src/akwb/cli.py`.
2. Accept `--project-root`, `--force`, `--depth minimal|standard|deep`, `--json`.
3. Validate project root exists.
4. Re-use existing `ConfigLoader` behavior.
5. Exit codes:
   - `0` success
   - `1` general error
   - `2` invalid configuration
   - `3` unsupported project
   - `4` analysis partially failed
   - `10` plugin error

**Acceptance:** `akwb analyze --help` displays usage. Running on a project
without the rest of Sprint 7 still exits with a clear "not yet implemented"
message until later tasks land.

---

## Task 2: Wire `ExtractionPipeline` into `Container`

**Owner:** Kernel / DI  
**Priority:** Critical

1. Import `ExtractionPipeline` and `KnowledgeFramework` in `src/akwb/container.py`.
2. Instantiate `ExtractionPipeline` in `Container.__init__`.
3. Ensure `Container.load_plugins()` extends the pipeline with plugin-provided
   readers, segmenters, extractors, builders, and validators.

**Acceptance:** `Container` exposes `extraction_pipeline` attribute. Unit test
verifies pipeline is configured with built-in Markdown reader and default
extractor.

---

## Task 3: Wire `GraphEngine` into `Container`

**Owner:** Kernel / DI  
**Priority:** Critical

1. Import `GraphEngine` in `src/akwb/container.py`.
2. Instantiate `GraphEngine` in `Container.__init__`.
3. Share the same `KnowledgeFramework` instance with `ExtractionPipeline`.
4. Ensure `Container.load_plugins()` extends the graph engine with plugin
   storage, query, traversal, and index backends.

**Acceptance:** `Container` exposes `graph_engine` attribute. Unit test verifies
graph engine builds from a sample catalog.

---

## Task 4: Load Plugins in CLI Flow

**Owner:** CLI  
**Priority:** Critical

1. Call `container.load_plugins()` before `discover` and `analyze`.
2. Surface plugin loading diagnostics in CLI output.
3. Continue analysis even if some plugins fail to load (record diagnostics).

**Acceptance:** Integration test uses a fixture plugin and confirms it is
loaded and used during `akwb discover` and `akwb analyze`.

---

## Task 5: Implement `AnalyzeEngine` Orchestrator

**Owner:** Kernel  
**Priority:** Critical

1. Create `src/akwb/analysis/engine.py` (or equivalent) that coordinates:
   - Discovery
   - Extraction
   - Catalog assembly
   - Graph build
   - Validation
   - Persistence
2. The engine must not contain parser/extractor logic. It orchestrates existing
   components.

**Acceptance:** Unit test analyzes a Markdown file and returns a
`KnowledgeGraph`.

---

## Task 6: Read Artifacts and Run Extraction

**Owner:** Analysis  
**Priority:** Critical

1. Iterate over `ArtifactRegistry` entries.
2. Skip unsupported/binary files with a diagnostic.
3. Read file bytes from the project root.
4. Call `ExtractionPipeline.extract(artifact, content, project_id=...)`.
5. Collect all `ExtractionResult`s and diagnostics.

**Acceptance:** Integration test analyzes a project with `README.md` and a `.py`
file and returns extracted objects.

---

## Task 7: Assemble `KnowledgeCatalog`

**Owner:** Knowledge Framework  
**Priority:** Critical

1. Create `KnowledgeCatalog` via `KnowledgeFramework.new_catalog()`.
2. Add all extracted `KnowledgeObject`s.
3. Add built-in relationship types.
4. Add synthetic `contains` relationships from source file to each object.

**Acceptance:** Catalog round-trips through `JsonlSerializer` and contains at
least one object and one relationship.

---

## Task 8: Build and Validate `KnowledgeGraph`

**Owner:** Graph Engine  
**Priority:** Critical

1. Call `GraphEngine.build(catalog)`.
2. Call `GraphEngine.validate(graph)`.
3. Call `GraphEngine.statistics(graph)` for diagnostics.
4. Record graph validation diagnostics.

**Acceptance:** Graph builds from a sample catalog, validates, and has an
index.

---

## Task 9: Implement `LocalGraphStorage`

**Owner:** Graph / Storage  
**Priority:** Critical

1. Create `src/akwb/graph/storage.py` with `LocalGraphStorage` implementing the
   `GraphStorage` port.
2. Write `graph_nodes.jsonl`, `graph_edges.jsonl`, `graph.dot`, `graph.cypher`
   to `.akwb/graph/`.
3. Implement `load()` to read `graph_nodes.jsonl` and `graph_edges.jsonl`.
4. Register `LocalGraphStorage` as a built-in graph storage plugin.

**Acceptance:** Graph save and load round-trip test passes. DOT and Cypher
files are non-empty.

---

## Task 10: Persist Workspace Artifacts

**Owner:** Workspace  
**Priority:** Critical

1. Move `artifacts.json` under `.akwb/index/source_catalog.jsonl` (or keep
   `artifacts.json` and add JSONL copy).
2. Write `knowledge/catalog.jsonl` or `knowledge/graph_nodes.jsonl` and
   `knowledge/graph_edges.jsonl`.
3. Write `graph/graph.jsonl`, `graph/graph.dot`, `graph/graph.cypher`.
4. Write `reports/summary.md` and `reports/summary.json`.
5. Update `workspace.json` manifest with artifact list.

**Acceptance:** After `akwb analyze`, all listed files exist and validate
against documented schemas.

---

## Task 11: Add `akwb report` Command

**Owner:** CLI  
**Priority:** High

1. `akwb report summary` prints/outputs JSON with object count, edge count, and
   diagnostics.
2. `akwb report structure` lists node types and counts.
3. `akwb report graph` prints a DOT preview.
4. Support `--output` and `--format`.

**Acceptance:** CLI tests for each report on an analyzed project.

---

## Task 12: Add `akwb export` Command

**Owner:** CLI  
**Priority:** High

1. `akwb export jsonl` writes/prints `graph_nodes.jsonl` + `graph_edges.jsonl`.
2. `akwb export dot` writes/prints `graph.dot`.
3. `akwb export cypher` writes/prints `graph.cypher`.
4. Support `--output`.

**Acceptance:** CLI tests for each format on an analyzed project.

---

## Task 13: Basic Python Source-Code Parser

**Owner:** Extraction  
**Priority:** High

1. Add `PythonReader` that returns a source AST representation.
2. Add `PythonSegmenter` or AST-to-segment mapper.
3. Add `PythonExtractor` that emits `component` (module/class) and `function`
   objects with source spans.
4. Emit `contains` relationships (module → class → function).
5. Emit `depends_on` relationships from top-level imports.

**Acceptance:** `akwb analyze` on a project with `src/app.py` produces at least
one `component` or `function` object from that file.

---

## Task 14: End-to-End Integration Test

**Owner:** QA / Integration  
**Priority:** Critical

1. Create fixture project with `README.md`, `src/app.py`, `tests/test_app.py`.
2. Run `akwb init`, then `akwb analyze` using `CliRunner`.
3. Assert exit code `0`.
4. Assert `.akwb/` contains expected artifacts.
5. Assert graph has at least one edge.
6. Assert `akwb report summary` and `akwb export jsonl` work.

**Acceptance:** Test passes and is added to CI.

---

## Task 15: Update Workspace Manifest on Analyze

**Owner:** Workspace  
**Priority:** Medium

1. After `analyze`, update `workspace.json` with:
   - `last_analysis_at`
   - `artifact_count`
   - `object_count`
   - `relationship_count`
   - `akwb_version`
2. Ensure `UnitOfWork.commit()` is used to stage and commit the manifest.

**Acceptance:** Unit test verifies manifest fields after analysis.

---

## Task 16: Documentation and Acceptance Criteria

**Owner:** Docs  
**Priority:** High

1. Update `docs/SPRINT_7_REPORT.md` after completion.
2. Update `docs/KNOWN_LIMITATIONS.md` with any deferred features.
3. Confirm `docs/MVP_ACCEPTANCE_TEST.md` scenarios pass.

**Acceptance:** Product owner runs the acceptance test manually and signs off.

---

## Sprint Exit Criteria

1. `akwb init` and `akwb analyze` run on a sample project.
2. `.akwb/` contains workspace manifest, source catalog, knowledge catalog,
   graph artifacts, and reports.
3. `akwb report` and `akwb export` commands work.
4. End-to-end integration test passes.
5. `python3 -m pytest -q` passes.
6. No architecture changes and no Constitution violations.
