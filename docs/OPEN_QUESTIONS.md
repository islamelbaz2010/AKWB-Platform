# Architecture Decisions

## Purpose
Track unresolved architectural decisions that must be closed before feature implementation proceeds.

## How to Use This Document
Each question has an impact, a recommended owner, a proposed decision, and a deadline. These questions are the acceptance criteria for the Foundation Sprint 1 readiness gate.

## Closed Decisions

All architecture decisions were closed by `ARCHITECTURE_FREEZE_v1.md`.

| # | Question | Impact | Owner | Final Decision | Status |
|---|---|---|---|---|---|
| 1 | What is the implementation language/runtime? | Drives packaging, concurrency, GIL handling, plugin model, and performance baseline. | Principal Engineer / Tech Lead | **Python 3.12**; optional Rust extensions for proven hot paths only. | Closed |
| 2 | What is the plugin runtime isolation model? | Security, packaging, performance, and crash containment. | Security Architect / Plugin Lead | **Python plugins run in-process with path sandboxing; `wasm`/`executable` plugins run in separate processes via JSON-RPC; high-risk plugins optionally in OS sandboxes.** | Closed |
| 3 | What are the concrete plugin port request/response schemas? | Plugin SDK, contract tests, marketplace, and cross-version compatibility. | Principal Engineer | **Typed Python protocols/ABCs with Pydantic/dataclass request/response models.** `docs/PLUGIN_API_SPEC.md` to detail ports. | Closed |
| 4 | Which storage backend should be used? | Performance, queryability, workspace size, and concurrency. | Storage / Performance Lead | **`StoragePort` abstraction with `LocalStorageBackend` default; JSONL for streaming collections, SQLite for indexes/metadata, JSON for manifests.** | Closed |
| 5 | What is the default AI/embedding/summarization model strategy? | AI engine dependencies, privacy, disk size, and network policy. | AI Lead | **Embeddings and summarization are optional and off by default; local-first if enabled; external models require explicit opt-in.** | Closed |
| 6 | What is the telemetry, error-reporting, and update-check policy? | Security, privacy, compliance, and user trust. | Security / Product Owner | **All telemetry, crash reporting, and update checks are opt-in and disabled by default; no project data transmitted.** | Closed |
| 7 | How are cross-language relationships resolved? | Knowledge graph completeness for mixed-language repositories. | Knowledge Engine Lead | **Use file paths, package names, import maps, and detector-provided alias tables; `RelationshipBuilder` plugins extend as needed.** | Closed |
| 8 | What is the canonical set of fixture projects and golden outputs? | Testing, contract tests, plugin validation, and regression detection. | QA / Test Lead | **`fixtures/python`, `fixtures/nodejs`, `fixtures/mixed`, `fixtures/docs-only`, and `fixtures/large`; golden output format defined in `ARCHITECTURE_FREEZE_v1.md`.** | Closed |
| 9 | What is the workspace schema migration strategy? | Backward compatibility and upgrade path across releases. | Data Model Lead | **Migration hooks keyed by `schemaVersion` in `workspace.json`; `akwb migrate` command for major bumps.** | Closed |
| 10 | What is the threat model for plugin execution and the marketplace? | Security architecture and sandbox design. | Security Architect | **`docs/THREAT_MODEL.md` must be produced in Sprint 1; sandbox is defense-in-depth with path validation, signatures, and resource watchdog.** | Closed |
| 11 | How is the plugin marketplace authenticated and signed? | Supply-chain security and trust. | Security / Release Lead | **Plugins signed with Sigstore/cosign or minisign; marketplace metadata signed by AKWB release key; marketplace is future work, gated by API stability.** | Closed |
| 12 | What is the exact CLI structured output schema and versioning? | Scripting, IDE integrations, and backward compatibility. | CLI Lead | **`cli-output-schema-v1.json` with `schemaVersion: "cli-output-v1"`, command, summary, artifacts, diagnostics.** | Closed |

## Decision Log
| Decision | Date | Owner | Status |
|---|---|---|---|
| Workspace lives inside `.akwb/` by default; external path via `--output` | Sprint 0 | Architecture Team | Closed |
| JSONL + SQLite hybrid for streaming and queryable persistence | Sprint 0 | Architecture Team | Closed |
| Least-privilege plugin permissions; no network by default | Sprint 0 | Architecture Team | Closed |
| Incremental, content-addressable analysis | Sprint 0 | Architecture Team | Closed |
| Implementation language: Python 3.12 | Architecture Freeze v1 | Architecture Team | Closed |
| Seven first-class engines: Discovery, Knowledge, Graph, Memory, AI, Workspace, Incremental | Architecture Freeze v1 | Architecture Team | Closed |
| Plugin API v1: typed Python protocols/ABCs, Pydantic/dataclass models | Architecture Freeze v1 | Architecture Team | Closed |
| Storage model: `StoragePort` with `LocalStorageBackend`; JSONL + SQLite + JSON + YAML | Architecture Freeze v1 | Architecture Team | Closed |
| Telemetry policy: opt-in, disabled by default, no project data | Architecture Freeze v1 | Security / Product | Closed |
| Embedding strategy: optional, off by default, local-first | Architecture Freeze v1 | AI Lead | Closed |
| Caching strategy: content-addressable parse/extract cache, fingerprint index, LRU eviction | Architecture Freeze v1 | Performance Lead | Closed |
| Workspace ownership: project owns `.akwb/`, AKWB never holds data | Architecture Freeze v1 | Architecture Team | Closed |
| Output format: plain files (JSONL, JSON, SQLite, Markdown, DOT, Cypher), versioned schemas | Architecture Freeze v1 | Architecture Team | Closed |
| Configuration model: defaults/global/project/env/CLI precedence, Pydantic validation, snapshot | Architecture Freeze v1 | Config Lead | Closed |
| Marketplace signing: Sigstore/cosign or minisign; metadata signed by AKWB release key | Architecture Freeze v1 | Security / Release | Closed |
| CLI output schema: `cli-output-schema-v1.json` | Architecture Freeze v1 | CLI Lead | Closed |
