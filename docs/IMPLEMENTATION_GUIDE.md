# Implementation Guide

## 1. Purpose

This guide provides implementation conventions, technology choices, and coding rules for building the AKWB Platform according to `ARCHITECTURE_FREEZE_v1.md`. It is **not** implementation code; it is the set of rules and patterns that all implementation work must follow.

## 2. Technology Stack

> **1.0.0 MVP implementation note:** Several advanced technologies listed below (Rust extensions, embeddings, sentence-transformers, ONNX Runtime) are **POST-MVP / PLANNED** and not used in the 1.0.0 MVP. The MVP uses pure Python 3.12, `click`, `pydantic`, filesystem/JSONL storage, and an in-memory event bus.

| Layer | Technology | Rationale |
|---|---|---|
| Language | **Python 3.12** | Frozen by Architecture v1; rich ecosystem; rapid iteration. |
| CLI framework | `typer` or `click` | Type-hint friendly; testable commands. |
| Configuration | `pydantic` + YAML/JSON | Strong validation; env var mapping; snapshotting. |
| Data models | `pydantic` `BaseModel` or Python `dataclasses` | Strong typing; serialization; schema generation. |
| Storage | `sqlite3` (stdlib), JSONL, filesystem | No heavy dependencies; inspectable. |
| Event bus | Custom typed in-memory bus | Lightweight; no external broker dependency. |
| DI container | Manual constructor injection or `dependency-injector` | Keeps domain pure; testable. |
| Testing | `pytest` | Standard; fixtures; parametrization. |
| Lint/format | `ruff`, `mypy` | Fast; modern; type checking. |
| Optional hot paths | Rust extensions via `maturin`/`PyO3` | **POST-MVP / PLANNED:** Only for proven bottlenecks (fingerprinting, parsing). |
| Embeddings (optional) | `sentence-transformers` or `onnxruntime` | **POST-MVP / PLANNED:** Local-first; no network by default. |

## 3. Repository Layout

> **1.0.0 MVP implementation note:** The current repository layout is flatter than the originally planned structure below. The 1.0.0 MVP source lives under `src/akwb/` and contains `analysis/`, `cli.py`, `config.py`, `container.py`, `discovery/`, `domain/`, `events/`, `extraction/`, `graph/`, `knowledge/`, `observability/`, `plugins/`, `storage/`, `types.py`, and `workspace/`. The full layout below reflects the long-term architecture; modules and directories marked **POST-MVP / PLANNED** are not present in 1.0.0.

```
akwb-platform/
├── pyproject.toml              # build, deps, entry points
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SUPPORT.md
├── docs/                       # extensive markdown documentation
├── src/
│   └── akwb/                   # 1.0.0 MVP source
│       ├── __init__.py         # version
│       ├── __main__.py         # python -m akwb entry
│       ├── cli.py              # CLI (1.0.0)
│       ├── config.py           # configuration loader (1.0.0)
│       ├── container.py        # DI composition root (1.0.0)
│       ├── _version.py         # version constant
│       ├── analysis/           # analysis engine (1.0.0)
│       ├── discovery/          # artifact discovery (1.0.0)
│       ├── domain/             # ports and core models (1.0.0)
│       ├── events/             # in-memory event bus (1.0.0)
│       ├── extraction/         # readers, segmenters, extractors (1.0.0)
│       ├── graph/              # graph engine (1.0.0)
│       ├── knowledge/          # knowledge object framework (1.0.0)
│       ├── observability/      # logging (1.0.0)
│       ├── plugins/            # plugin loader and registry (1.0.0)
│       ├── storage/            # local filesystem storage (1.0.0)
│       ├── types.py            # shared types (1.0.0)
│       └── workspace/          # workspace bootstrap (1.0.0)
│       ├── kernel/             # **POST-MVP / PLANNED**
│       ├── reporting/          # **POST-MVP / PLANNED**
│       ├── security/           # **POST-MVP / PLANNED**
│       └── unit_of_work/       # **POST-MVP / PLANNED**
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── fixtures/
└── scripts/
```

## 4. Coding Standards

- **Python 3.12 features:** use `typing` generics (e.g., `list[str]`), union (`|`), and `Self` where appropriate.
- **Type hints:** all public functions and methods must have type hints. `mypy --strict` is the target.
- **No `print` in core code:** use `akwb.observability` for all logging/progress.
- **No module-level side effects:** no network, filesystem, or import side effects at module import time.
- **Immutability:** prefer frozen Pydantic models or dataclasses for value objects.
- **Error handling:** use `Result[T, Diagnostic]` or exceptions for unrecoverable errors; never swallow failures.
- **Path handling:** use `pathlib.Path` everywhere; no string paths in domain.

## 5. Clean Architecture Rules

1. `akwb.domain` and `akwb.types` have **no** internal AKWB imports.
2. Engines depend on `domain` ports and `events`/`observability`; they do not import `cli`, `kernel`, or each other.
3. `akwb.storage` implements repository interfaces declared in `akwb.domain`.
4. `akwb.plugins` loads plugin code through `domain` ports; core never statically imports a plugin.
5. `akwb.cli` depends only on `akwb.kernel`, `akwb.config`, and `akwb.reporting`.
6. No cyclic imports. Run `python -m akwb` to verify at build time.

## 6. Dependency Injection Convention

Use constructor injection for all application and adapter classes:

```python
class DiscoveryEngine:
    def __init__(
        self,
        config: Config,
        plugin_registry: PluginRegistry,
        event_bus: EventBus,
        observability: Observability,
    ) -> None:
        ...
```

The `akwb.kernel.DIContainer` is the single composition root for the CLI. It wires all implementations based on config.

## 7. Domain Modeling Rules

- **Entities** have identity and mutable state only through domain methods.
- **Value objects** are immutable; equality is based on value, not identity.
- **Aggregates** have a single root entity and enforce invariants.
- **Domain events** are immutable dataclasses with `event_id`, `timestamp`, `correlation_id`, and `version`.
- **Repository interfaces** live in `akwb.domain` and are implemented by `akwb.storage`.
- **Result type:** use `akwb.types.Result[T, Diagnostic]` for operations that can partially fail.

## 8. Engine Implementation Patterns

Each engine:

1. Implements a domain `Engine` port or abstract class.
2. Receives dependencies via constructor injection.
3. Publishes domain events through the `EventBus`.
4. Returns an aggregate or artifact; does not write to workspace directly (except Workspace Engine).
5. Is idempotent: same inputs → same outputs.
6. Supports `--force` full run and incremental selective run.

### 8.1 Discovery Engine

- Implement `FileWalker` utility using `pathlib` and `os.scandir`.
- Implement `Fingerprinter` using `hashlib.sha256`.
- `Detector` plugins return `DetectionResult` with confidence scores.
- Classification merges detector outputs by confidence and priority.

### 8.2 Knowledge Engine

- `Parser` plugins return a `ParsedModel` (language-specific AST/doc model).
- `Extractor` plugins traverse `ParsedModel` and emit `KnowledgeUnit`s and `Relationship`s.
- `DependencyExtractor` plugins process manifest files.
- Use streaming: do not hold all `ParsedModel`s in memory.
- Cache parsed models by source content hash.

### 8.3 Knowledge Graph Engine

- Consume `KnowledgeUnit`/`Relationship` stream.
- Use `IdentityResolver` to merge duplicates by qualified name + source span.
- Build in-memory graph; spill to SQLite when node/edge count exceeds `graphMaxMemory`.
- Build adjacency and inverted indexes in SQLite.
- Export `graph.jsonl`, `graph.dot`, `graph.cypher`.

### 8.4 Memory Engine (POST-MVP / PLANNED)

- Walk `KnowledgeGraph` and generate facts (e.g., "UserService has 5 methods").
- Generate per-unit summaries and project-wide summary.
- Write `memory/facts.jsonl` and `memory/summaries.json`.

> **1.0.0 MVP Status:** Not implemented.

### 8.5 AI Context Engine (POST-MVP / PLANNED)

- Use Memory summaries as input.
- Chunk source text and summaries by token budget.
- If `enableEmbeddings` is true, compute local embeddings and build vector index.
- Build `ContextBundle` per task and write `context/context_bundles.jsonl`.

> **1.0.0 MVP Status:** Not implemented.

### 8.6 Workspace Engine

- Collect artifacts from all engines.
- Stage writes in `.akwb/staging/`.
- Render reports using `Reporter` plugins.
- Promote staging to workspace by updating `workspace.json` atomically.

> **1.0.0 MVP Status:** Artifacts are written directly to `.akwb/` via the `AnalyzeEngine` and `LocalStorageBackend`. Two-phase staging, `Reporter` plugins, and atomic promotion are **POST-MVP / PLANNED.**

### 8.7 Incremental Engine

- Load previous `SourceCatalog` and fingerprints.
- Compute new fingerprints and diff.
- Build invalidation graph: source → knowledge unit → artifact.
- Propagate invalidation through the graph.

> **1.0.0 MVP Status:** Fingerprint-based change detection and registry diffing are implemented. Invalidation graph propagation is **POST-MVP / PLANNED.**

## 9. Event Bus Rules

- Events are immutable Pydantic/dataclass instances.
- Event handlers must not block; heavy work is delegated back to engines.
- The `EventBus` is in-process only; remote brokers are a future adapter.
- Do not use events as commands; commands go through `Kernel` scheduling.

## 10. Plugin Authoring Guide

A minimal plugin package:

```
akwb-python/
  plugin.yaml
  pyproject.toml
  src/
    akwb_python/
      __init__.py
      parser.py
      extractor.py
      plugin.py
```

`plugin.py`:

```python
from akwb.plugins import PluginAPI
from akwb.ports import ParserPort, ExtractorPort
from akwb_python.parser import PythonParser
from akwb_python.extractor import PythonExtractor

def register(api: PluginAPI) -> None:
    api.register_port(ParserPort, PythonParser)
    api.register_port(ExtractorPort, PythonExtractor)

def capabilities() -> dict:
    return {"ports": ["Parser", "Extractor"], "languages": ["python"]}

def health() -> dict:
    return {"ok": True}
```

- Plugins must declare `plugin_api_version` and `akwb_compat`.
- Plugins must define `permissions` explicitly.
- Plugins should not write files directly; use the provided `StoragePort`.
- Plugins must handle parse/extraction errors and return `Diagnostic` objects.

## 11. Storage Backend Implementation

`LocalStorageBackend` responsibilities:

- Implement repository interfaces from `akwb.domain`.
- Read/write JSONL, JSON, YAML, SQLite.
- Atomic writes: temp file in same directory + rename.
- Maintain `workspace.json` and `ArtifactManifest`.
- Support staging directory for two-phase commit.
- Support content-addressable cache.

Future storage backends implement the same `StoragePort` and `*Repository` interfaces.

## 12. Security Implementation Checklist

> **1.0.0 MVP Status:** Only canonical path validation in `LocalStorageBackend` and disabled-by-default telemetry are implemented. All other checklist items are **POST-MVP / PLANNED.**

- [x] Canonical path validation before any plugin file read. **Implemented in 1.0.0.**
- [ ] Permission check before network, execute, or out-of-project access. **POST-MVP / PLANNED.**
- [ ] Signature verification for remote plugins or plugins requesting `network`/`execute`. **POST-MVP / PLANNED.**
- [ ] Secret scanning before writing any artifact. **POST-MVP / PLANNED.**
- [ ] Audit logging for plugin load, network, execute, config change, and security violations. **POST-MVP / PLANNED.**
- [ ] Resource watchdog enforcing CPU time, memory, and file-size limits. **POST-MVP / PLANNED.**
- [x] No project data in telemetry even when enabled. **Implemented in 1.0.0 (telemetry is disabled by default).**

## 13. Testing Conventions

- **Unit tests:** domain logic, pure functions, no I/O.
- **Engine tests:** each engine with `MemoryStorageBackend` and stub plugins.
- **Contract tests:** each plugin against port-specific fixtures and golden outputs.
- **Integration tests:** end-to-end analysis of fixture projects.
- **Performance tests:** run on `fixtures/large`; fail on >10% regression.
- **Security tests:** malformed plugins, sandbox escape attempts, secret scanning.

Use `pytest` fixtures for `Config`, `EventBus`, `Observability`, `MemoryStorageBackend`, and stub plugins.

## 14. Performance Guidelines

> **1.0.0 MVP Status:** The current implementation is single-threaded and loads full file/catalog contents into memory. The guidelines below are the long-term target; they are **POST-MVP / PLANNED** for 1.0.0.**

- Use process pools for CPU-bound parsing where the GIL is a bottleneck. **POST-MVP / PLANNED.**
- Use thread pools for I/O-bound file walking and fingerprinting. **POST-MVP / PLANNED.**
- Stream JSONL writes; avoid loading full collections into memory. **POST-MVP / PLANNED.**
- Use bounded queues between engines to apply backpressure. **POST-MVP / PLANNED.**
- Monitor peak memory with `tracemalloc` in profiling mode. **POST-MVP / PLANNED.**
- Keep workspace size under 2x source size by default. **Target for post-MVP benchmarking.**

## 15. Observability Requirements

- Structured logs in JSON or text with correlation IDs. **Partially implemented in 1.0.0 as text logs.**
- Progress events for CLI rendering. **POST-MVP / PLANNED.**
- Metrics: files/sec, units/sec, cache hit rate, peak memory, duration per phase. **POST-MVP / PLANNED.**
- `--profile` writes a phase timing breakdown. **POST-MVP / PLANNED.**
- Diagnostics are first-class artifacts with `level`, `code`, `message`, and `sourceRef`. **Implemented in 1.0.0.**

## 16. Documentation Requirements

Every module, engine, and plugin port must have:

- A docstring explaining purpose and public interface.
- A `README.md` in the module directory for non-trivial modules.
- ADRs for any deviation from `ARCHITECTURE_FREEZE_v1.md`.

## 17. Definition of Done for Implementation Tickets

- [ ] Code follows style guide and passes `ruff` and `mypy`. **Target for 1.0.0; see release verification for current status.**
- [x] Unit or engine tests added; all tests pass. **Implemented in 1.0.0.**
- [x] No new cyclic dependencies. **Implemented in 1.0.0.**
- [x] Public interfaces documented. **Implemented in 1.0.0.**
- [x] No hardcoded paths, languages, or model assumptions in core. **Implemented in 1.0.0.**
- [ ] Security and privacy rules respected. **Partially implemented in 1.0.0 (local-first, disabled telemetry, path sandboxing). Hardened plugin sandboxing and secret scanning are POST-MVP / PLANNED.**
- [x] Change reviewed against `ARCHITECTURE_FREEZE_v1.md`.
