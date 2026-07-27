# Publishing Implementation Roadmap

## Purpose

Sequence the implementation work for the Publishing Architecture extension after approval.

## Phase P1: Foundation (Sprint P1 — Domain Models & Plugin Ports)

Goal: Define the publishing bounded context in code without implementing business logic, parsers, or AI.

- Create `akwb/domain/publishing/` package with value objects and aggregates:
  - `ProjectUnderstanding`, `ProjectProfile`, `ProjectTypeEvidence`, `Signal`
  - `KnowledgeDomain`, `DomainRelevance`, `DomainSelection`
  - `DocumentKind`, `DocumentCandidate`, `PlannedDocument`, `DocumentPlan`
  - `GeneratedDocument`, `ContentBlock`, `Provenance`, `SourceReference`
  - `PublishingManifest`, `ExportPackage`, `ExportTarget`, `ExportResult`, `ExportTargetSpec`
- Create `akwb/domain/publishing/ports.py` with ABCs:
  - `ProjectTypeDetector`
  - `DomainContributor`
  - `StrategyContributor`
  - `PublishingRule`
  - `DocumentPlanner`
  - `DocumentGenerator`
  - `Exporter`
  - `KnowledgeClassifier`
  - `SourceConnector` (optional)
  - `TraceabilityEnricher` (optional)
- Add `publishing` section to `Config` and `ConfigLoader`.
- Add `akwb/engines/publishing/` package skeleton with engines:
  - `PublishingEngine`
  - `ProjectUnderstandingEngine`
  - `AdaptivePublishingStrategyEngine`
  - `PublishingRulesEngine`
  - `DocumentPlanningEngine`
  - `ExportEngine`
- Add `Publishing*` domain events to `akwb.domain.events`.
- Add unit tests for domain object validation and event emission.

Deliverable: Domain models, ports, and engine skeletons compile and pass unit tests; no real plugins yet.

## Phase P2: Reference Plugins (Sprint P2 — Validate Ports)

Goal: Implement minimal reference plugins to exercise the ports and ensure the contracts are sound.

- Create a reference `akwb-publishing-defaults` plugin package (in `plugins/` or as a separate test fixture):
  - Default `KnowledgeDomain` definitions (`foundation`, `business`, `engineering`, etc.)
  - A simple `ProjectTypeDetector` (matches file patterns, e.g., `package.json` → `software-platform`)
  - A simple `StrategyContributor` (emits candidates for detected domains)
  - A pass-through `PublishingRule` (no transformation)
  - A `DocumentPlanner` that topologically sorts by dependencies
  - A `DocumentGenerator` that produces `GeneratedDocument` with one placeholder `ContentBlock`
  - A `MarkdownExporter` and a `JsonExporter` for `workspace` and `local_path` targets
- Add contract tests that instantiate each engine with reference plugins.
- Ensure `PublishingEngine` orchestrates the pipeline and emits events in order.
- Validate `PublishingManifest` is produced and persisted.

Deliverable: A minimal end-to-end publishing pipeline that runs against a fixture project and produces artifacts.

## Phase P3: Project Understanding & Strategy Hardening (Sprint P3)

Goal: Improve accuracy and configurability of project-type detection and document strategy.

- Implement signal aggregation and confidence scoring.
- Add configuration for `project_type_detector_threshold`, `domain_confidence_threshold`, `strategy_confidence_threshold`, and `strategy_weights`.
- Implement user overrides: `publishing.force_documents`, `publishing.suppress_documents`, `publishing.force_domains`, `publishing.excluded_domains`.
- Add diagnostics for low-confidence, conflict, and missing context.
- Write fixture-based tests for mixed project types (e.g., a software project with `investment/` directory).

Deliverable: Project understanding and strategy produce stable, configurable, and tested candidate lists.

## Phase P4: Document Planning & Traceability (Sprint P4)

Goal: Robust planning, dependency resolution, and traceability.

- Implement `DocumentPlan` dependency graph, cycle detection, and topological sort.
- Implement `PublishingRulesEngine` with rule ordering and lineage tracking.
- Implement `ContentBlock` and `Provenance` chains in `GeneratedDocument`.
- Wire `TraceabilityEnricher` plugins for cross-reference resolution.
- Add tests for merge/split/version/supersede rules and provenance preservation.

Deliverable: Document plans are validated, ordered, and explainable; every generated block has provenance.

## Phase P5: Export Architecture & Incremental Integration (Sprint P5)

Goal: Make exports real, idempotent, and incremental.

- Implement `ExportEngine`, `ExporterRegistry`, and target resolution.
- Implement `MarkdownExporter`, `JsonExporter` for workspace and local path targets.
- Integrate `PublishingManifest` with the Incremental Engine / `ArtifactManifest` diff pattern.
- Implement `regenerate` flag propagation and skip unchanged exports.
- Add `ExportResult` fingerprints to `PublishingManifest`.
- Add tests for incremental export (same inputs → no re-write; changed inputs → re-export).

Deliverable: The full pipeline is incremental and produces artifacts in user-specified formats and locations.

## Phase P6: Integration, CLI, and Hardening (Sprint P6)

Goal: Wire publishing to the CLI and existing engines.

- Add `akwb publish` CLI command (or extend `akwb analyze` with publishing stage).
- Integrate with `Container`, `PluginRegistry`, and `WorkspaceBootstrap`.
- Validate `StoragePort` sandbox for workspace exports and permission checks for external exports.
- Add contract tests with fixture projects.
- Update documentation: `docs/07_DISCOVERY_ENGINE.md`, `09_WORKSPACE_ENGINE.md`, etc., to reference publishing pipeline.

Deliverable: CLI runs the publishing end-to-end; integration tests pass.

## Phase P7: Documentation & Quality Gate (Sprint P7)

Goal: Complete the publishing architecture implementation and certify quality.

- Write `docs/publishing/IMPLEMENTATION_NOTES.md` summarizing plugin contracts.
- Add `ARCHITECTURE_FREEZE_v1.1_PUBLISHING.md` ratifying the extension.
- Run full test suite and benchmarks.
- Update `ARCHITECTURE_SCORE.md` with post-implementation scores.

Deliverable: Publishing architecture is production-ready and merged.

## Milestones

| Milestone | Target | Acceptance Criteria |
|---|---|---|
| M1 | End of P1 | Domain models and ports compile; unit tests pass. |
| M2 | End of P2 | End-to-end pipeline with reference plugins produces artifacts. |
| M3 | End of P4 | Planning, rules, and traceability are fully tested. |
| M4 | End of P6 | CLI integration and integration tests pass. |
| M5 | End of P7 | Documentation and quality gate complete. |

## Dependencies on Existing Sprints

- Requires **Discovery Foundation** to be production-ready (completed).
- Requires **Knowledge/Graph/Memory/AI engines** to exist as consumers of `SourceCatalog` and `KnowledgeGraph` (architecture defined, implementation in future sprints).
- `ExportEngine` reuses `StoragePort` and `WorkspaceEngine` persistence.
- `PublishingEngine` reuses `EventBus`, `Observability`, `Container`, and `PluginRegistry`.

## Risk Mitigation

- **Freeze v1 engine restriction:** Get `Architecture v1.1 Publishing Extension` approval before P1.
- **Plugin contract churn:** Use reference plugins in P2 to harden port signatures before P3–P5.
- **Incremental correctness:** Build incremental export tests early in P5; reuse existing `ArtifactManifest` diff logic.
- **Traceability storage bloat:** Normalize provenance into `trace_index.jsonl`/`graph_index.sqlite` when P4 benchmarks show bloat.

## Recommendation

Proceed with Phase P1 after user approval of the Publishing Architecture v1.1 extension.
