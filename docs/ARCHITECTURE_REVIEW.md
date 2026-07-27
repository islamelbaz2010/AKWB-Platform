# Architecture Review

## Executive Summary

AKWB Sprint 0 produced a coherent, Clean Architecture / Domain-Driven Design-based design for a local-first, project-owned, CLI-driven knowledge workspace. The architecture is sound at a high level and has strong security, extensibility, and incremental-processing properties. However, several implementation-critical gaps were identified. Targeted improvements have been applied directly to the Sprint 0 documents, and the remaining gaps are tracked in `OPEN_QUESTIONS.md`.

The architecture is **ready for a Foundation Sprint 1** whose purpose is to close implementation-language, plugin-runtime, plugin-contract, storage, AI-model, and telemetry decisions while building the repository skeleton. It is **not ready for feature implementation** (parsers, extractors, AI context, marketplace) until those gates are closed.

## Strengths

- **Local ownership:** the project owns its `.akwb/` workspace; the platform never holds project data.
- **Plugin extensibility:** new languages and frameworks are supported through a versioned port architecture.
- **Incremental processing:** content-addressable fingerprints and an invalidation graph avoid full re-analysis.
- **Clean Architecture / DDD:** clear boundaries between Domain, Engines, Adapters, and Infrastructure.
- **Security by default:** least-privilege plugins, no network by default, secret redaction, and signed plugins for elevated permissions.
- **Strong non-functional requirements:** explicit performance, scalability, maintainability, and testability targets.

## Per-Document Gap Analysis and Applied Improvements

| Document | Gaps Identified | Improvements Applied |
|---|---|---|
| `01_PRODUCT_VISION.md` | Minor: AI/embedding optionality not explicit. | Reviewed; no critical changes required. |
| `02_PRODUCT_REQUIREMENTS.md` | Missing `init`, `doctor`, `--check`, telemetry opt-in, plugin API compatibility. | Added FRs 13–17 and design decisions for onboarding, diagnostics, dry-run, telemetry, and plugin API validation. |
| `03_SYSTEM_ARCHITECTURE.md` | Missing Event Bus, Unit of Work, Observability/Diagnostics as first-class components; no transaction boundaries. | Added Event Bus, Unit of Work, and Observability components; defined commit/rollback flow. |
| `04_DOMAIN_MODEL.md` | Missing repository interfaces, `ArtifactManifest`, `Package`/`Dependency`, `Result`/`Diagnostic`, `IdentityResolver`. | Added repository ports, artifact manifest aggregate, dependency entities, diagnostics, and identity resolution service. |
| `05_MODULES.md` | Missing `akwb.events`, `akwb.observability`, `akwb.unit_of_work`. | Added modules and updated dependency rules. |
| `06_PLUGIN_ARCHITECTURE.md` | Missing runtime isolation, package format, API versioning, capability introspection, signature mechanism, conflict resolution. | Added design decisions for packaging, isolation, `plugin_api_version`, capabilities, signatures, and conflict resolution. |
| `07_DISCOVERY_ENGINE.md` | Missing project root detection, encoding detection, default ignore patterns, filter precedence, dependency manifest tagging, generated-dir heuristics. | Added root detection, encoding detection, default ignores, filter precedence, and generated-directory detection. |
| `08_KNOWLEDGE_ENGINE.md` | Missing entity resolution, `TraceabilityBuilder`, cross-language links, dependency extraction, graph algorithms. | Added `IdentityResolver`, `TraceabilityBuilder`, cross-language resolution, dependency extraction, and graph algorithm hooks. |
| `09_WORKSPACE_ENGINE.md` | Missing `ArtifactManifest` as source of truth, staging/recovery, report templating, schema version. | Added staging, transaction journal, workspace recovery, report templating, and schema-version decisions. |
| `10_AI_ENGINE.md` | Missing `ContextRetrievalAPI`, task selection, summarization fallback, token budget enforcement. | Added context API, task selection, fallback summarization, and token budget enforcement. |
| `11_DATA_MODEL.md` | Missing `ArtifactManifest`, `Package`/`Dependency`, repository interfaces, `EventEnvelope`, schema version, kind registries. | Added schemas/ports for artifact manifest, packages, events, schema versioning, and kind registries. |
| `12_CONFIGURATION.md` | Missing environment variable mapping, `configVersion`, default ignore patterns, plugin schema validation. | Added `AKWB_*` env mapping, `configVersion`, default ignores, and plugin config validation. |
| `13_CLI_SPECIFICATION.md` | Missing `init`, `doctor`, `--check`, environment variable mapping, structured output schema. | Added commands and conventions for `init`, `doctor`, `--check`, env vars, and `--json` schema versioning. |
| `14_INCREMENTAL_ANALYSIS.md` | Missing plugin/version invalidation, config invalidation, rename detection strategy, manifest lineage. | Added invalidation rules for plugin versions, configuration changes, rename handling, and snapshot lineage. |
| `15_STORAGE_MODEL.md` | Missing staging, transaction journal, recovery, backup/restore. | Added staging area, transaction journal, recovery logic, and backup/restore design decisions. |
| `16_SECURITY_MODEL.md` | Missing signature mechanism, audit integrity, telemetry policy, runtime isolation, resource watchdog, secret scanning details. | Added Sigstore/minisign signing, audit log chained hashes, telemetry opt-in, runtime isolation, resource watchdog, and secret scanning patterns. |
| `17_PERFORMANCE_STRATEGY.md` | Missing GIL/backpressure, batch sizes, memory-mapped files, adaptive workers, graph size budget. | added Python GIL considerations, bounded queues/backpressure, batch sizing, memory-mapped reads, adaptive worker pools, and graph size budgets. |
| `18_TESTING_STRATEGY.md` | Missing CI matrix, contract harness, benchmarking harness, property/mutation tests. | Added CI matrix, plugin contract harness, benchmarking harness, and property/mutation test guidance. |
| `19_RELEASE_STRATEGY.md` | Missing CI/CD, SBOM, reproducible builds, artifact signing, changelog automation. | Added CI/CD pipeline, SBOM, reproducible builds, artifact signing, and changelog automation. |
| `20_ROADMAP.md` | Missing Sprint 0 gate, readiness gates, dependency gating. | Added approval gate, phase readiness gates, and dependency gating for marketplace and enterprise features. |

## Remaining Architecture Gaps

> **Note:** All gaps below were closed by `ARCHITECTURE_FREEZE_v1.md`. The freeze document contains the final decisions. This section is retained for Sprint 0 review context.

1. **Implementation language/runtime not selected.** Drives packaging, concurrency, and plugin packaging.
2. **Plugin port request/response contract not formalized.** Needs concrete schemas, lifecycle hooks, and error contracts.
3. **Storage backend not decided at Sprint 0 (closed by `ARCHITECTURE_FREEZE_v1.md`: SQLite + JSONL).**
4. **AI/embedding model strategy unresolved.** Local vs. remote, licensing, size, and privacy impact need closure.
5. **Telemetry, error-reporting, and update-check policy not documented.** Required before any network code.
6. **No formal threat model.** Needed for plugin execution and marketplace security.
7. **No canonical fixture set or golden outputs.** Blocks contract testing and plugin validation.
8. **Workspace schema migration strategy is high-level.** Need migration hooks and `akwb migrate` plan.
9. **Cross-language relationship resolution heuristics undefined.** Important for mixed-language repositories.
10. **Graph query/index design is high-level.** Need concrete index structures and query API.

## Scalability & Performance Risks

- The 1M LOC / <5 min target assumes efficient parser/extractor worker pools; actual performance depends on parser quality and batch/backpressure control.
- In-memory knowledge graphs for large repositories may exceed the 4 GB memory target; spilling to SQLite and lazy loading are defined but not validated.
- Parallel parsing of 100k+ files can exhaust file descriptors or memory if `maxWorkers` and batch sizes are not tuned.
- Large JSONL files are hard to query without secondary indexes; indexes must be built before reports are generated.

## Security Risks

- In-process Python plugins cannot be fully sandboxed by path validation alone; OS-level isolation or WASM is required for untrusted code.
- Secret scanning has false negatives; redaction is a safety net, not a substitute for removing secrets from source.
- Plugin marketplace and remote install introduce supply-chain risk; signing and SBOM are defined but not yet implemented.
- Any network code for telemetry or update checks without an explicit policy would violate the privacy non-functional requirement.

## Developer Experience Issues

- `akwb init`, `akwb doctor`, and `akwb analyze --check` are now required but need full command specs and messages.
- Error/diagnostic output needs a structured schema so users and CI can act on failures.
- `.akwb/` can grow large; `.gitignore` guidance and cleanup commands must be prominent in onboarding.
- Plugin authors need a reference SDK and contract-test harness before the ecosystem can grow.

## Plugin Architecture Issues

- Port API versioning (`plugin_api_version`) is documented but the actual request/response schemas and lifecycle hooks are not.
- Plugin package format (wheel, zip, directory) and entry-point loading need a concrete specification.
- Conflict resolution between overlapping detectors or extractors needs deterministic, user-overridable rules.
- Plugin runtime isolation (in-process vs. subprocess vs. WASM) must be chosen before plugins can be safely loaded.

## Future Extensibility

- Clean boundaries and ports support remote workers, cloud storage, IDE extensions, web dashboards, and marketplace without core rewrites.
- Event-driven design and `EventEnvelope` support watch mode, real-time updates, and event replay.
- Schema versioning and migration hooks support long-term workspace compatibility.
- The `Package`/`Dependency` model enables future SBOM, vulnerability, and supply-chain features.

## Recommendations

1. **Do not begin feature implementation** until the five critical decisions (language/runtime, plugin contract, storage, AI model, telemetry policy) are closed.
2. Create a formal `PLUGIN_API_SPEC.md` with request/response schemas, lifecycle hooks, and a reference plugin SDK.
3. Produce a `THREAT_MODEL.md` before any network or plugin-install code is written.
4. Build canonical fixtures and a contract-test harness in Foundation Sprint 1.
5. Validate the 1M LOC / 5 min target with a benchmarking harness as soon as the storage backend is chosen.
6. Document telemetry, error-reporting, and update-check policy explicitly.
7. Lock the workspace `schemaVersion` and migration contract before the first public beta.

## Conclusion

Sprint 0 architecture is a strong, de-risked foundation. The applied improvements close most documentation gaps and provide enough guidance for Foundation Sprint 1. Feature implementation should be gated by the readiness criteria in `READY_FOR_SPRINT_1.md` and the decisions in `ARCHITECTURE_FREEZE_v1.md`.
