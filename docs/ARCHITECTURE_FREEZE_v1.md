# AKWB Architecture Freeze v1

## 1. Purpose

This document is the **Architecture Freeze** for the AKWB Platform. Once approved, the core architecture is frozen for the lifetime of Architecture Version 1. Implementation may begin. Core engines, modules, data flows, CLI commands, plugin ports, storage model, workspace layout, and configuration model may only be modified through the **Architecture Version 2** process. All extension must occur through the plugin API defined herein.

## 2. Final Architecture

### 2.1 Architectural Layers (Clean Architecture, inside-out)

| Layer | Responsibility | Modules |
|---|---|---|
| **Domain** | Entities, value objects, domain events, repository interfaces, domain services, invariants. | `akwb.domain`, `akwb.types` |
| **Application** | Use-case orchestration; engines and kernel. | `akwb.kernel`, `akwb.engines.*`, `akwb.unit_of_work` |
| **Adapter** | Plugin system, CLI, storage backends, report renderers, AI adapters. | `akwb.cli`, `akwb.plugins`, `akwb.storage`, `akwb.reporting` |
| **Infrastructure** | OS/filesystem, process execution, optional network, logging, metrics. | `akwb.events`, `akwb.observability`, `akwb.security` |

**Dependency rule:** dependencies point inward. Outer layers depend on inner layers; the Domain layer has no dependencies on any other AKWB module.

### 2.2 Core Components

- **Kernel:** Parses CLI input, loads and merges configuration, initializes the DI container, validates plugins, schedules engines, manages the Unit of Work, and publishes lifecycle events.
- **Event Bus:** Lightweight, typed, in-process publish/subscribe bus for domain events. It decouples engines; it is not an external message broker.
- **Unit of Work:** Coordinates repository operations across an analysis run. All artifacts are staged; the workspace manifest is only promoted on success.
- **Observability:** Structured logging, metrics, progress events, diagnostics, and profiling hooks. Cross-cutting; used by every module.
- **Security:** Secret scanning, plugin signature verification, sandbox path validation, permission enforcement, audit logging.
- **Storage Backend:** Implements repository ports. `LocalStorageBackend` is the default; future backends implement the same ports.

### 2.3 Final Engine List

AKWB has **seven first-class engines**. Each engine is a bounded use case, owns a specific aggregate or artifact, and may be scheduled, skipped, or extended independently through plugins.

| # | Engine | Primary Responsibility | Input | Output | Rationale |
|---|---|---|---|---|---|
| 1 | **Discovery Engine** | Scan project, detect profiles, classify sources, fingerprint files, build `SourceCatalog`. | Project path, config, prior `SourceCatalog`, `Detector` plugins. | `SourceCatalog`, change set, `SourceDiscovered`/`SourceClassified` events. | Required first step; produces the canonical source inventory. |
| 2 | **Knowledge Engine** | Parse and extract `KnowledgeUnit`s and `Relationship`s from sources. | `SourceCatalog`, `Parser`/`Extractor`/`DependencyExtractor` plugins, prior cache. | Stream of `KnowledgeUnit`s and `Relationship`s, `KnowledgeExtracted` events. | Core extraction engine; language-agnostic through plugins. |
| 3 | **Knowledge Graph Engine** | Assemble, deduplicate, index, and query the `KnowledgeGraph`; export graph artifacts. | `KnowledgeUnit`s, `Relationship`s, `RelationshipBuilder` plugins. | `KnowledgeGraph` aggregate, graph indexes, `graph/` exports, `GraphBuilt` event. | Central artifact of the platform; deserves a dedicated lifecycle. |
| 4 | **Memory Engine** | Generate durable project memory: facts, summaries, and entity lookup indexes. | `KnowledgeGraph`, `SourceCatalog`. | `memory/facts.jsonl`, `memory/summaries.json`, `memory.index`, `MemoryProduced` event. | Separates long-term memory from ephemeral AI context. |
| 5 | **AI Context Engine** | Build token-aware, task-specific `ContextBundle`s, summaries, chunks, and optional embeddings. | `KnowledgeGraph`, `Memory`, `ContextBuilder` plugins, configuration. | `ContextBundle` artifacts, chunks, vector/keyword indexes, `ContextProduced` event. | Distinct from Memory: task-oriented, optional, and model-specific. |
| 6 | **Workspace Engine** | Materialize artifacts, render reports, manage the `.akwb/` workspace and manifest. | All engine artifacts, `Reporter` plugins, config. | Updated `.akwb/` workspace, `workspace.json`, `ArtifactProduced`/`WorkspaceSealed` events. | The boundary between analysis and the project-owned workspace. |
| 7 | **Incremental Engine** | Compare fingerprints, compute change sets, propagate invalidation, manage snapshots. | Prior and current `SourceCatalog`, artifact manifest, config. | Change set, invalidation list, new `Snapshot`, `SnapshotCreated` event. | Foundation of performance; crosses all engines. |

### 2.4 Engine Evaluation

#### Engines that ARE first-class

| Engine | Why it is first-class |
|---|---|
| **Workspace Engine** | Already first-class. Owns the `.akwb/` workspace, manifest, two-phase commit, and report materialization. No other engine writes project files. |
| **AI Context Engine** | Already first-class (as AI Engine). Owns task-specific context, chunking, optional embeddings, and RAG. Distinct from general project memory. |
| **Knowledge Graph Engine** | Promoted to first-class. The graph is the central artifact; it needs assembly, deduplication, indexing, query, and export logic independent of extraction. This keeps `KnowledgeEngine` focused on parsing/extraction and `WorkspaceEngine` focused on persistence. |
| **Memory Engine** | New first-class engine. Project memory (facts, summaries, entity index) is a long-lived, semantic artifact. Separating it from AI Context prevents model-specific chunking/embedding logic from leaking into the project's durable memory. |
| **Incremental Engine** | Promoted from "manager" to engine. Fingerprinting, change detection, invalidation propagation, and snapshot management are a distinct use case that spans all other engines. |

#### Proposed engines that are NOT first-class

| Proposed Engine | Why it is NOT first-class | What it becomes |
|---|---|---|
| **Normalization Engine** | Parsing and normalization are stages inside the `KnowledgeEngine`. A separate engine would persist an intermediate AST/CIR, complicate incremental invalidation, and duplicate `KnowledgeEngine` responsibilities. | `Parser` and optional `Normalizer` plugin ports inside `KnowledgeEngine`. |
| **Evidence Engine** | Evidence is a cross-cutting domain concept, not an engine. Every relationship, artifact, and diagnostic carries evidence. | `Evidence` value object and `EvidenceCollector` domain service used by `KnowledgeEngine`, `GraphEngine`, and `TraceabilityBuilder` plugins. |
| **Traceability Engine** | Traceability is a specialized graph-building activity. It adds edges to the `KnowledgeGraph` and is best implemented as a `RelationshipBuilder`/`TraceabilityBuilder` plugin port consumed by the `KnowledgeGraphEngine`. | `TraceabilityBuilder` plugin port. May become a first-class engine in Architecture v2 if requirements-management features are added. |
| **Validation Engine** | Validation is a quality gate, not a runtime engine. It is performed by `akwb doctor`, contract tests, schema validators, and each engine's own validation. | Validation rules embedded in `akwb.doctor`, engine pipelines, and plugin contract tests. |
| **Dependency Analysis Engine** | Dependency extraction is a specialized extraction task. Manifest files are sources like any other. A separate engine would duplicate `KnowledgeEngine` responsibilities. | `DependencyExtractor` plugin port inside `KnowledgeEngine`; produces `Package`/`Dependency` entities in the `KnowledgeGraph`. |

### 2.5 Quality Gate: Engine Check

- [x] No duplicated responsibilities across engines.
- [x] Every engine has a single, bounded input and output.
- [x] `KnowledgeEngine` extracts; `KnowledgeGraphEngine` assembles and indexes; `WorkspaceEngine` persists.
- [x] `MemoryEngine` generates durable project memory; `AIContextEngine` generates task-specific context.
- [x] `IncrementalEngine` owns change detection and invalidation.
- [x] No engine directly calls another engine; all coordination is through the `EventBus` and `Kernel` scheduler.

## 3. Final Module List

| Module | Responsibility | Allowed Dependencies |
|---|---|---|
| `akwb` | Entry point, version, signal handling. | `akwb.cli` |
| `akwb.cli` | Argument parsing, command dispatch, progress rendering, exit codes. | `akwb.kernel`, `akwb.config`, `akwb.reporting`, `akwb.observability` |
| `akwb.kernel` | Orchestrator: DI container, engine scheduling, lifecycle, UoW. | `akwb.domain`, `akwb.engines.*`, `akwb.plugins`, `akwb.storage`, `akwb.events`, `akwb.observability`, `akwb.unit_of_work` |
| `akwb.config` | Configuration schemas, loading, merging, validation, env/CLI mapping. | `akwb.types` only |
| `akwb.domain` | Entities, value objects, events, repository interfaces, domain services. | `akwb.types` only |
| `akwb.types` | Shared constants, result types, serialization primitives, identifiers. | None (shared kernel) |
| `akwb.events` | Typed event bus, handlers, envelope serialization. | `akwb.types` only |
| `akwb.observability` | Logging, metrics, diagnostics, progress reporting. | `akwb.types`, `akwb.events` |
| `akwb.unit_of_work` | Transaction boundary, repository coordination, rollback. | `akwb.domain`, `akwb.storage` ports, `akwb.events` |
| `akwb.engines.discovery` | Discovery Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability`, `akwb.security` |
| `akwb.engines.knowledge` | Knowledge Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability`, `akwb.security`, `akwb.plugins` ports |
| `akwb.engines.graph` | Knowledge Graph Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability`, `akwb.storage` |
| `akwb.engines.memory` | Memory Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability` |
| `akwb.engines.ai` | AI Context Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability`, `akwb.storage` (for optional models) |
| `akwb.engines.workspace` | Workspace Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability`, `akwb.storage`, `akwb.reporting` |
| `akwb.engines.incremental` | Incremental Engine implementation. | `akwb.domain`, `akwb.events`, `akwb.observability`, `akwb.storage` |
| `akwb.plugins` | Plugin loader, registry, lifecycle, sandbox, contract validation. | `akwb.domain` ports, `akwb.config`, `akwb.security`, `akwb.observability` |
| `akwb.storage` | Storage backend implementations, local workspace I/O, repository implementations. | `akwb.domain` (implements ports), `akwb.types`, `akwb.security` |
| `akwb.reporting` | Report rendering, output formatting (human-readable and structured). | `akwb.domain`, `akwb.storage` |
| `akwb.security` | Secret scanning, signature verification, sandbox enforcement, audit logging. | `akwb.domain` ports, `akwb.types`, `akwb.observability` |

### Quality Gate: Module Check

- [x] No cyclic dependencies.
- [x] `domain` and `types` do not depend on any other AKWB module.
- [x] Engines depend on `domain` ports, not on other engines directly.
- [x] `cli` does not depend on engines or plugins.
- [x] Every module has unambiguous ownership.

## 4. Final Folder Structure

### 4.1 Repository Source Tree

```
akwb-platform/
├── pyproject.toml
├── README.md
├── docs/
│   ├── architecture/
│   └── ...
├── src/
│   └── akwb/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       ├── config/
│       ├── domain/
│       ├── engines/
│       │   ├── discovery/
│       │   ├── knowledge/
│       │   ├── graph/
│       │   ├── memory/
│       │   ├── ai/
│       │   ├── workspace/
│       │   └── incremental/
│       ├── events/
│       ├── observability/
│       ├── kernel/
│       ├── plugins/
│       ├── reporting/
│       ├── security/
│       ├── storage/
│       ├── types/
│       └── unit_of_work/
├── tests/
│   ├── unit/
│   ├── engine/
│   ├── contract/
│   ├── integration/
│   ├── security/
│   └── fixtures/
├── fixtures/
│   ├── python/
│   ├── nodejs/
│   ├── mixed/
│   ├── docs-only/
│   └── large/
└── scripts/
```

### 4.2 `.akwb/` Workspace Layout

```
<project>/.akwb/
  workspace.json                  # manifest, schemaVersion, snapshot id
  config/
    effective_config.json         # snapshot of merged configuration
  index/
    source_catalog.jsonl          # SourceEntry records
    file_fingerprints.json        # path -> fingerprint map
  knowledge/
    graph_nodes.jsonl             # KnowledgeUnit records
    graph_edges.jsonl             # Relationship records
    graph_index.sqlite            # adjacency + inverted + kind indexes
  memory/
    facts.jsonl                   # derived facts
    summaries.json                # entity summaries
    memory.index                  # keyword/entity lookup
  context/
    context_bundles.jsonl         # ContextBundle records
    chunks/                       # chunk files keyed by id
    vector.index                  # optional vector index
  reports/
    structure.md
    coverage.md
    knowledge_graph.md
    summary.json
  graph/
    graph.jsonl                   # canonical node/edge export
    graph.dot
    graph.cypher
  cache/
    parsed/                       # content-addressable parsed models
    extracted/                    # content-addressable extraction results
  logs/
    analysis.log
    audit.log
    transaction.log
  staging/                        # two-phase commit staging area
```

## 5. Final Data Flow

### 5.1 Normal Analysis Flow (`akwb analyze <path>`)

1. **CLI** parses command, project path, and flags.
2. **Kernel** loads configuration from defaults, global, project, `AKWB_*` env vars, and CLI flags; validates schema; stores effective snapshot.
3. **Kernel** initializes the DI container: `EventBus`, `UnitOfWork`, `Observability`, `StorageBackend`, `PluginRegistry`.
4. **Plugin Registry** discovers plugins from `AKWB_PLUGIN_PATH` and config, validates manifests/signatures/permissions, registers ports.
5. **Storage** loads previous `workspace.json` and `SourceCatalog` if present.
6. **Incremental Engine** computes fingerprints for the current filesystem, diffs against prior `SourceCatalog`, and emits a `ChangeSet` plus invalidation list.
7. **Discovery Engine** scans the project (full if `--force`, selective if incremental), applies ignore/include patterns, classifies sources, builds new `SourceCatalog`.
8. **Knowledge Engine** parses and extracts only changed/invalidated `SourceEntry`s (plus their transitive dependents). Emits `KnowledgeUnit`s and `Relationship`s.
9. **Knowledge Graph Engine** consumes the stream, deduplicates via `IdentityResolver`, assembles `KnowledgeGraph`, builds graph indexes, exports `graph/` artifacts.
10. **Memory Engine** consumes `KnowledgeGraph` and `SourceCatalog`; generates `memory/facts.jsonl` and `memory/summaries.json`.
11. **AI Context Engine** consumes `KnowledgeGraph`, `Memory`, and `ContextBuilder` plugins; generates `ContextBundle`s, chunks, and optional vector index.
12. **Workspace Engine** plans reports, invokes `Reporter` plugins, stages all artifacts in `.akwb/staging/`.
13. **Unit of Work** validates the staged workspace; on success promotes to `.akwb/` and updates `workspace.json`; on failure rolls back.
14. **Observability** emits metrics, diagnostics, and progress events.
15. **CLI** prints summary, artifact paths, and exit code.

### 5.2 Dry-Run Flow (`akwb analyze --check`)

Same flow as normal, except:
- Staging is not promoted.
- No files are written to `.akwb/` (except temporary staging that is deleted after validation).
- Output is a JSON/YAML plan describing what would change.

## 6. Final CLI Design

### 6.1 Commands

| Command | Purpose |
|---|---|
| `akwb init [<path>]` | Create `.akwb/` with default config and `.gitignore` guidance. |
| `akwb doctor` | Validate environment, plugins, permissions, disk space, and config. |
| `akwb analyze [<path>]` | Run full or incremental analysis. |
| `akwb update` | Alias for `akwb analyze .` incremental. |
| `akwb status` | Show workspace state, changed files, missing plugins, size. |
| `akwb config <key> [<value>]` | Get/set/list configuration. |
| `akwb report <name>` | Generate a specific report. |
| `akwb plugin <list|install|remove|verify>` | Manage plugins. |
| `akwb clean [--cache-only|--all]` | Remove cache or all derived artifacts. |
| `akwb version` | Show CLI, plugin API, and workspace format versions. |
| `akwb migrate` *(future)* | Upgrade workspace to current schema version. |

### 6.2 Common Flags

| Flag | Description |
|---|---|
| `--config <path>` | Use specific config file. |
| `--depth minimal|standard|deep` | Override knowledge extraction depth. |
| `--plugin <id>` | Load specific plugin; repeatable. |
| `--ignore <pattern>` | Additional ignore pattern; repeatable. |
| `--no-ai` | Skip AI Context Engine. |
| `--no-memory` | Skip Memory Engine. |
| `--no-graph` | Skip graph export generation. |
| `--force` | Ignore incremental state; full analysis. |
| `--check` | Dry-run; report planned changes without writing. |
| `--output <dir>` | Write workspace to custom directory. |
| `--format <md|json|html>` | Report output format. |
| `--json` | Structured CLI output. |
| `--quiet` | Suppress progress. |
| `--verbose` | Increase logging. |
| `--profile` | Dump timing breakdown. |

### 6.3 Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | General error |
| `2` | Invalid configuration |
| `3` | Unsupported project / no applicable plugins |
| `4` | Analysis partially failed (diagnostics emitted) |
| `5` | Security / permission error |
| `10` | Plugin error |

### 6.4 Environment Variables

- `AKWB_CONFIG`: path to global config directory.
- `AKWB_PLUGIN_PATH`: additional plugin search paths (colon-separated).
- `AKWB_*`: maps to dotted config keys. Example: `AKWB_DISCOVERY_MAX_FILE_SIZE` overrides `discovery.maxFileSize`.

### 6.5 Structured Output Schema

`--json` output follows `cli-output-schema-v1.json`:

```json
{
  "schemaVersion": "cli-output-v1",
  "command": "analyze",
  "project": "/path/to/project",
  "exitCode": 0,
  "success": true,
  "summary": {
    "filesAnalyzed": 1200,
    "unitsExtracted": 5400,
    "relationships": 8900,
    "artifacts": 12,
    "durationSeconds": 45
  },
  "artifacts": ["reports/structure.md", "context/context_bundles.jsonl"],
  "diagnostics": []
}
```

## 7. Final Plugin API

### 7.1 Plugin Ports (v1)

All ports are Python protocols/ABCs. Request/response models are Pydantic/dataclass instances.

| Port | Request | Response | Owner Engine |
|---|---|---|---|
| **Detector** | `ProjectContext` | `DetectionResult` (profiles, confidence, ignore hints) | Discovery |
| **Parser** | `SourceEntry` | `ParsedModel` (normalized AST/doc structure) | Knowledge |
| **Extractor** | `ParsedModel` | `ExtractionResult` (units, relationships, diagnostics) | Knowledge |
| **DependencyExtractor** | `SourceEntry` (manifest file) | `DependencyResult` (packages, dependencies) | Knowledge |
| **RelationshipBuilder** | `KnowledgeGraph`, `SourceCatalog` | list of `Relationship` | Graph |
| **ContextBuilder** | `ContextRequest` (task, graph, memory) | `ContextBundle` | AI |
| **Reporter** | `ReportRequest` (name, artifacts, format) | `ReportContent` (bytes + mime type) | Workspace |
| **Exporter** | `KnowledgeGraph`, target format | `bytes` | Workspace (via Graph) |
| **StorageBackend** | `Artifact` / query | persisted data | Storage (future) |

### 7.2 Plugin Manifest (`plugin.yaml`)

```yaml
id: com.example.python
name: Python Support
version: 1.2.0
author: Example Inc
license: MIT
plugin_api_version: "1.0.0"
akwb_compat: ">=1.0.0,<2.0.0"
ports:
  - port: Parser
    priority: 100
  - port: Extractor
    priority: 100
entrypoint: akwb_python.plugin
runtime: python
config_schema: config_schema.json
permissions:
  filesystem: read
  network: false
  execute: false
  secrets: false
  out_of_project_read: false
signature: ...
```

### 7.3 Runtime Models

- **Python plugins:** loaded in-process via import. Path sandboxing enforced by core.
- **WASM / executable plugins:** spawned as subprocesses. Core communicates via JSON-RPC over stdin/stdout.
- **Script plugins:** shims for external tools; run in subprocess with timeout and output capture.

### 7.4 Lifecycle Hooks

A plugin module must expose:

```python
def register(api: PluginAPI) -> None:
    api.register_port(ParserPort, MyParser)

def capabilities() -> dict:
    return {"ports": ["Parser", "Extractor"], "languages": ["python"]}

def health() -> HealthResult:
    return HealthResult(ok=True)
```

### 7.5 Permission Model

| Permission | Default | Requires Signature |
|---|---|---|
| `filesystem:read` | true | no |
| `filesystem:write` | false (writes go through StoragePort) | no |
| `network` | false | yes |
| `execute` | false | yes |
| `secrets` | false | yes |
| `out_of_project_read` | false | yes |

### 7.6 Versioning and Conflict Resolution

- `plugin_api_version` declared by plugin; core rejects incompatible plugins.
- `akwb_compat` SemVer range defines compatible AKWB versions.
- Port priority resolves overlapping plugins; user config overrides priority.
- Multiple plugins may implement the same port; core selects by priority and capability match.

## 8. Final Storage Strategy

### 8.1 Storage Abstraction

The `StoragePort` in `domain` abstracts all persistence. The default `LocalStorageBackend` writes to `.akwb/`.

### 8.2 Persistence Formats

| Format | Used For |
|---|---|
| **JSONL** | Streaming collections: `SourceEntry`, `KnowledgeUnit`, `Relationship`, `Fact`, `ContextBundle`. |
| **SQLite** | Indexes and relational lookups: graph adjacency, inverted keyword, file fingerprints, invalidation graph. |
| **JSON** | Manifests and configuration snapshots. |
| **YAML** | Human-authored configuration. |
| **Markdown** | Human-readable reports. |
| **Binary** | Optional vector indexes (`vector.index`) and content-addressable cached models. |

### 8.3 Atomicity and Two-Phase Commit

1. New artifacts are written to `.akwb/staging/`.
2. SQLite index updates occur inside a transaction.
3. On success, `workspace.json` manifest is updated atomically via temp file + rename.
4. On failure, staging is discarded and `workspace.json` is unchanged.
5. Recovery on startup replays `logs/transaction.log` and removes orphaned files.

### 8.4 Caching Strategy

- **Parsed cache:** `cache/parsed/{sha256}` keyed by source content hash.
- **Extracted cache:** `cache/extracted/{sha256}-{extractorVersion}` keyed by source fingerprint and extractor version.
- **Fingerprint index:** `index/file_fingerprints.json`.
- **Artifact reuse:** unchanged artifacts are referenced by fingerprint in `ArtifactManifest`.
- **Eviction:** LRU by size and age; configurable `cacheMaxSize` and `cacheMaxAge`.

### 8.5 Retention and Cleanup

- `akwb clean --cache-only` removes `cache/`.
- `akwb clean` removes `cache/`, `reports/`, `context/`, `memory/`, `graph/` but keeps `config/` and latest manifest.
- `akwb clean --all` removes all of `.akwb/`.
- Logs rotated by size and count.

## 9. Final Workspace Layout

See section 4.2 for the full directory tree. Rules:

- `workspace.json` is the single source of truth for the workspace state.
- `schemaVersion` in `workspace.json` is `1` for Architecture v1.
- All artifacts are referenced by `ArtifactManifest`.
- All paths inside the workspace are relative to the project root.
- The workspace is portable: copying `.akwb/` to another machine with the same project path works.

## 10. Final Output Layout

### 10.1 Artifact Conventions

| Artifact | Location | Format | Schema Version |
|---|---|---|---|
| Source catalog | `index/source_catalog.jsonl` | JSONL | v1 |
| Fingerprints | `index/file_fingerprints.json` | JSON | v1 |
| Graph nodes | `knowledge/graph_nodes.jsonl` | JSONL | v1 |
| Graph edges | `knowledge/graph_edges.jsonl` | JSONL | v1 |
| Graph index | `knowledge/graph_index.sqlite` | SQLite | v1 |
| Facts | `memory/facts.jsonl` | JSONL | v1 |
| Summaries | `memory/summaries.json` | JSON | v1 |
| Context bundles | `context/context_bundles.jsonl` | JSONL | v1 |
| Chunks | `context/chunks/{id}.json` | JSON | v1 |
| Vector index | `context/vector.index` | Binary/HNSW | v1 |
| Reports | `reports/{name}.{md|json}` | Markdown/JSON | v1 |
| Graph exports | `graph/graph.{jsonl|dot|cypher}` | JSONL/DOT/Cypher | v1 |

### 10.2 Naming Rules

- JSONL file names use plural nouns: `graph_nodes.jsonl`.
- Indexes use `.sqlite` or `.index` extensions.
- Cache files are content-addressable: `{sha256}` with optional extension.
- Chunk files use the chunk id as filename.

## 11. Final Configuration

### 11.1 Configuration Sources (lowest to highest precedence)

1. `akwb.defaults.yaml` (shipped with AKWB).
2. Global user config: `~/.config/akwb/config.yaml` (macOS/Linux) or `%APPDATA%\akwb\config.yaml` (Windows).
3. Project config: `.akwb/config.yaml` or `akwb.yaml`.
4. `AKWB_*` environment variables.
5. CLI flags.

### 11.2 Core Sections

```yaml
configVersion: 1

discovery:
  ignorePatterns: []
  includePatterns: []
  maxFileSize: 1048576
  maxDepth: 50
  followSymlinks: false
  useGitignore: true

knowledge:
  extractionDepth: standard  # minimal | standard | deep
  enabledExtractors: []
  relationshipConfidenceThreshold: 0.5
  parseTimeout: 30

graph:
  enableExports: true
  exportFormats: [jsonl, dot]

memory:
  enabled: true
  maxFactsPerUnit: 10

ai:
  enabled: true
  enableEmbeddings: false
  embeddingModel: sentence-transformers/all-MiniLM-L6-v2
  tokenBudget: 4000
  chunkSize: 512
  chunkOverlap: 64
  contextBuilders: []

workspace:
  outputFormats: [jsonl, markdown]
  enabledReports: [structure, coverage, summary]
  keepLogs: 5
  versioning: latest

plugins:
  pluginPath: []
  registryUrl: null
  autoLoad: true
  plugins: {}

security:
  allowNetwork: false
  allowExecute: false
  secretScanning: true
  pluginSignatureRequired: false

cache:
  maxSize: 1073741824  # 1 GB
  maxAge: 86400        # 24 hours
```

### 11.3 Environment Variable Mapping

- Prefix `AKWB_`.
- Dots become underscores. Example: `AKWB_DISCOVERY_MAX_FILE_SIZE` overrides `discovery.maxFileSize`.
- Lists are comma-separated. Example: `AKWB_PLUGINS_PLUGINPATH=/path1,/path2`.
- Booleans accept `true`/`false`, `1`/`0`, `yes`/`no`.

### 11.4 Validation

- Configuration is validated with Pydantic models.
- Unknown keys under `plugins.{pluginId}` are allowed if the plugin provides a schema.
- Invalid configuration fails fast with line numbers and actionable messages.
- Effective configuration is snapshot to `.akwb/config/effective_config.json`.

## 12. Architecture Constraints

- **Project-owned workspace:** AKWB never holds project data; `.akwb/` lives in the project.
- **Local-first:** No network by default; all network features are opt-in.
- **Plain files:** All workspace artifacts are plain, inspectable files (JSONL, JSON, YAML, SQLite, Markdown, DOT, Cypher).
- **Language-agnostic:** No language-specific logic in core; all language support is via plugins.
- **Clean boundaries:** Domain has no external dependencies; engines do not depend on each other directly.
- **Event-driven coordination:** Engines communicate through typed domain events, not direct calls.
- **Incremental by default:** Every analysis run is incremental unless `--force` is used.
- **AI optional:** Embeddings and external model calls are disabled by default.
- **Telemetry opt-in:** No telemetry, crash reporting, or update checks without explicit consent.
- **Secret redaction:** Secrets are redacted from all artifacts.

## 13. Architecture Rules

1. **Dependency Rule:** Source code dependencies always point inward toward `domain`. Outer layers may depend on inner layers; inner layers never depend on outer layers.
2. **No Cyclic Dependencies:** Module dependency graph is a DAG.
3. **Plugin Extensibility:** Core functionality is extended only through plugin ports. Core never imports plugin code directly.
4. **Idempotent Engines:** Running the same analysis twice with the same inputs produces the same artifacts.
5. **Immutable Snapshots:** Snapshots are immutable; workspace references a current snapshot.
6. **Content-Addressable Cache:** Cache keys are derived from content/version hashes, not paths.
7. **Least Privilege:** Plugins receive the minimum permissions required.
8. **Fail-Soft:** A plugin failure is recorded as a `Diagnostic`; analysis continues unless the failure is unrecoverable.
9. **Human-First CLI:** Default output is human-readable; `--json` is stable and versioned.
10. **Schema Versioning:** Every persisted artifact schema and the plugin API are versioned independently of the CLI version.

## 14. Backward Compatibility Rules

- **Workspace schema:** `schemaVersion` in `workspace.json` is incremented on breaking changes. Migration scripts must be provided for major bumps.
- **Plugin API:** `plugin_api_version` is incremented on breaking port changes. Old API plugins are supported for one minor CLI version with warnings.
- **CLI output:** `--json` output has a `schemaVersion` field. Consumers may request a specific schema version with `--json-schema v1`.
- **Configuration:** `configVersion` is incremented when required keys or default behavior change. Older configs are migrated automatically where possible.
- **CLI commands:** Major CLI behavior changes require a major CLI version bump (SemVer).

## 15. Extension Rules

- **New language support:** Add `Detector`, `Parser`, and `Extractor` plugins. No core changes.
- **New report:** Add a `Reporter` plugin and add the report name to `workspace.enabledReports`.
- **New AI task:** Add a `ContextBuilder` plugin.
- **New graph relationship type:** Add a `RelationshipBuilder` plugin or extend the kind registry.
- **New storage backend:** Implement the `StorageBackend` port.
- **New engine:** Not allowed in Architecture v1. Requires Architecture v2 proposal.
- **New core port:** Requires Architecture v2 unless it can be expressed as an existing plugin port.

## 16. Non-negotiable Decisions

| # | Decision | Rationale |
|---|---|---|
| 1 | **Implementation language: Python 3.12** | Given explicitly; fastest path to ecosystem, tooling, and plugin support. Optional Rust extensions for hot paths. |
| 2 | **`.akwb/` inside project root** | Project owns workspace; portable; matches Git/Docker mental model. |
| 3 | **Local-first, no network by default** | Privacy and security core tenet. |
| 4 | **SQLite + JSONL storage default** | Balances streaming and queryability; plain files for inspectability. |
| 5 | **Plugin API v1 in-process Python protocols; WASM/executable via subprocess** | Maximum performance for Python plugins; safe isolation for non-Python. |
| 6 | **Embeddings optional and off by default; local-first if enabled** | Privacy and disk-size control. |
| 7 | **Telemetry, error reporting, and update checks opt-in and off by default** | Privacy and trust. |
| 8 | **Seven first-class engines** | Discovery, Knowledge, Graph, Memory, AI, Workspace, Incremental. No others in v1. |
| 9 | **Clean Architecture with Domain at center** | 10-year maintainability, testability, and plugin isolation. |
| 10 | **Content-addressable incremental analysis** | Performance and correctness. |
| 11 | **Secret redaction in all artifacts** | Security. |
| 12 | **Schema versioning for workspace, plugin API, CLI output, and config** | Backward compatibility and safe evolution. |

## 17. Quality Gate Certification

Before this freeze is declared complete, the following were verified:

- [x] **No duplicated responsibilities:** each engine and module has a single owner.
- [x] **No cyclic dependencies:** module dependency graph is acyclic.
- [x] **No ambiguous module ownership:** every module has a clear public interface and responsibility.
- [x] **No missing workflow:** Discovery → Knowledge → Graph → Memory → AI → Workspace is complete; Incremental and validation gates wrap all steps.
- [x] **No missing engine:** the seven engines cover all required use cases.
- [x] **No undocumented outputs:** every artifact has a location, format, and schema version.
- [x] **No undocumented generated artifacts:** all `.akwb/` entries are listed in the workspace layout.
- [x] **No unresolved architecture decisions:** all open questions from `OPEN_QUESTIONS.md` are closed below or superseded by this freeze.
- [x] **No undefined extension points:** plugin ports are listed with request/response models and lifecycle hooks.

## 18. Approval

This Architecture Freeze v1 is ready for implementation approval. No core changes may be made after sign-off without an Architecture v2 proposal.
