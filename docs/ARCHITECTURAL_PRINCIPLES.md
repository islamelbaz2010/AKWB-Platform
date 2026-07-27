# AKWB Architectural Principles

**Version:** 1.0
**Status:** Ratified with the AKWB Constitution

This document expands the architectural principles of the AKWB Constitution
into practical guidance for architects, contributors, and reviewers. It is not
a code specification. It is a permanent statement of how the engine is built
and why.

---

## 1. Clean Boundaries

AKWB is organized around bounded contexts with explicit dependency rules. The
engine is not a monolith of convenience. Each module owns one responsibility,
calls only what it is allowed to call, and exposes only public contracts.

- `domain` and `types` have no internal AKWB dependencies.
- `engines` depend on `domain`, `types`, `incremental`, and `security`
  interfaces.
- `plugins` and `storage` implement `domain` ports.
- `cli` depends only on `kernel`, `config`, and `reporting`.
- No circular dependencies are permitted.

A module that cannot be deleted without pain is a module that is not properly
bounded.

---

## 2. Plugin-First Design

Every extensible surface is a port. Built-in implementations are first-class
plugins in spirit. The engine must be able to ship without a built-in
implementation and still function if a plugin supplies one.

Public ports include but are not limited to:

- `Reader` — converts raw bytes into `NormalizedContent`.
- `Segmenter` — breaks normalized content into `Segment`s.
- `Extractor` — produces `ExtractionCandidate`s.
- `CandidateBuilder` — builds `KnowledgeObject`s from candidates.
- `CandidateValidator` — validates candidates before building.
- `RelationshipBuilder` — adds cross-file, cross-language relationships.
- `GraphStorage` — persists and loads `KnowledgeGraph` artifacts.
- `GraphQueryEngine` — executes graph queries.
- `GraphTraversal` — runs graph traversals.
- `GraphIndexer` — indexes a graph for efficient query.
- `KnowledgeTypeProvider` — registers new knowledge types.
- `RelationshipTypeProvider` — registers new relationship types.
- `KnowledgeValidatorProvider` — registers additional validators.

No component may reach around a port. No component may prefer an internal
implementation over an equivalent plugin.

---

## 3. Local-First Architecture

The default architecture assumes no network. All external calls are explicit
and optional.

- Analysis reads local files.
- Workspace artifacts are local files.
- Cache is local.
- Plugins are loaded from local paths.
- Telemetry is off by default.

Remote storage, remote models, and remote telemetry may exist as plugins, but
the engine must remain fully functional without them.

---

## 4. Artifact-Centric Persistence

The engine persists state by writing versioned artifacts to `.akwb/`. It does
not expose a live service, a shared mutable cache, or an undocumented state
machine.

Artifacts are:

- **Self-describing** — each carries its schema version.
- **Append-only where possible** — JSONL for nodes, edges, facts, and source
  entries.
- **Atomic** — files are written to a temporary location and renamed into
  place.
- **Portable** — paths inside `.akwb/` are project-relative.
- **Inspectable** — human-readable formats are preferred.

The workspace is the single source of truth. Downstream products read the
workspace, not the engine process.

---

## 5. Deterministic and Reproducible Pipelines

A pipeline stage must be deterministic given:

- the same source inputs,
- the same configuration,
- the same plugin versions,
- the same AKWB version.

Non-determinism may only enter through:

- explicit external model calls,
- timestamp fields in workspace metadata,
- declared plugin behavior.

Even then, the engine must isolate and declare non-deterministic contributors.
Caching, fingerprinting, and incremental analysis depend on determinism.

---

## 6. Incremental by Default

The engine must not reprocess unchanged sources. Every stage supports
invalidation based on content-addressable fingerprints.

- Discovery fingerprints files by SHA-256 with mtime/size quick-skip.
- Extraction caches by `(source_fingerprint, extractor_version, plugin_version)`.
- Graph build invalidates nodes and edges whose source fingerprints changed.
- Reports are regenerated only when their inputs changed.

Incremental behavior is not an optimization. It is a correctness and scaling
requirement.

---

## 7. Evidence and Traceability

Every knowledge object and relationship must be traceable to source evidence.
Evidence includes:

- `source_refs` — file path and span.
- `evidence` — the specific text or node that supports the claim.
- `confidence` — a score when inference or heuristics are used.
- `provenance` — which plugin or extractor produced the object.
- `fingerprint` — the source content hash at the time of extraction.

No object may exist without evidence. No relationship may exist without source
support. Inferred relationships are allowed but must be labeled as such.

---

## 8. Least-Privilege Plugins

Plugins operate with the minimum authority required by their port. The engine
enforces declared permissions.

- A `Reader` needs `filesystem:read`.
- A `GraphStorage` plugin needs `workspace:write`.
- A network-capable plugin must explicitly declare `network:read` and be
  approved by the user.
- A plugin must not write outside `.akwb/` unless its permission includes
  `filesystem:write` and the path is inside the project root.

Permission violations cause the plugin to fail with a clear diagnostic. The
engine continues with other plugins.

---

## 9. Immutable Core Contracts

Core data contracts (`KnowledgeObject`, `KnowledgeRelationship`,
`KnowledgeCatalog`, `KnowledgeGraph`, `ArtifactEntry`, `SourceEntry`,
`WorkspaceManifest`) are value-oriented. They do not mutate in place.

- Operations produce new objects.
- Caches store immutable values.
- The graph aggregate exposes query and mutation methods, but individual nodes
  and edges are values.

Immutability makes caching, diffing, and concurrency safe.

---

## 10. Contract Stability Over Convenience

Public contracts change slowly. Internal implementation changes freely.

- Plugin ports are versioned.
- Artifact schemas are versioned.
- CLI output schemas are versioned.
- Data model identifiers are stable across versions where possible.

A contributor may refactor the engine, but may not silently break the workspace
format or plugin API.

---

## 11. Small CLI Surface

The CLI is intentionally small. Commands are engine operations, not product
workflows.

Primary commands:

- `akwb analyze <path>` — analyze a project and write the workspace.
- `akwb init [<path>]` — bootstrap a workspace.
- `akwb update` — incremental update of the current project.
- `akwb status` — inspect workspace state.
- `akwb report <name>` — generate a report artifact.
- `akwb export <format>` — export graph data.
- `akwb clean` — remove workspace artifacts and cache.
- `akwb doctor` — validate environment.
- `akwb config` — read and write configuration.
- `akwb plugin` — list and verify plugins.
- `akwb version` — print version.

Every new CLI command must be justified by the Constitution. Commands that
serve a downstream product workflow are rejected.

---

## 12. Error Continuity

The engine continues analysis when a single file or plugin fails. Failures are
recorded as diagnostics in the workspace, not fatal errors.

- Malformed files produce diagnostics, not crashes.
- Plugin failures produce diagnostics and disable the plugin for that run.
- Partial workspaces are valid and inspectable.
- Exit codes communicate severity: success, partial failure, complete failure,
  configuration error, security error.

Error continuity makes the engine robust in real projects with imperfect inputs.

---

## 13. Testability at the Contract Level

Tests must target public contracts, not implementation details.

- Every plugin port has a reference test suite.
- Every artifact schema has round-trip tests.
- Every CLI command has fixture-based tests.
- Determinism tests compare output against golden artifacts.

Tests that depend on internal class structure are fragile and are discouraged.

---

## 14. Observability Without Exposure

The engine reports progress, diagnostics, and metrics. It does not expose
source content, secrets, or sensitive metadata in logs.

Observability is for:

- debugging analysis failures,
- measuring performance,
- verifying plugin behavior,
- auditing workspace writes.

It is not for surveillance, marketing, or remote profiling.

---

## 15. Refactoring Favor

The architecture prefers refactoring over new abstraction. Before adding a new
engine, module, or layer, ask:

- Can an existing engine absorb this responsibility?
- Can this be a plugin instead of a core module?
- Does this require a new abstraction, or can it be a function?

Abstractions are added when the cost of not adding them is higher than the cost
of maintaining them.

---

## 16. Summary

The AKWB architecture is:

- **Bounded** — clear module responsibilities.
- **Plugin-based** — extensible through public ports.
- **Local-first** — no network required.
- **Artifact-centric** — the workspace is the contract.
- **Deterministic** — reproducible outputs.
- **Incremental** — fingerprint-driven invalidation.
- **Traceable** — evidence before inference.
- **Secure by default** — least-privilege plugins.
- **Stable** — contracts evolve carefully.
- **Small** — the CLI and core remain narrow.

These principles protect the engine from scope creep and make it a durable
foundation for downstream products.
