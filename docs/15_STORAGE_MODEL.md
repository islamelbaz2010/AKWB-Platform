# Storage Model

## Purpose
Specify how AKWB reads, writes, indexes, and archives project workspace data on local and future remote storage.

## Responsibilities
- Define the storage abstraction and backend implementations.
- Define the workspace directory layout.
- Define caching, atomic write, and consistency semantics.
- Define retention and cleanup policies.

## Storage Abstraction
The `StoragePort` defined in `domain` abstracts all persistence. Implementations:
- `LocalStorageBackend` (default): writes to `.akwb/`.
- `MemoryStorageBackend` (for tests and ephemeral runs).
- Future: `S3StorageBackend`, `RemoteStorageBackend`, `ArchiveStorageBackend`.

## Local Workspace Storage
- **Metadata:** `workspace.json` manifest; `config/` effective configuration snapshot.
- **Index:** `index/source_catalog.jsonl`, `index/file_fingerprints.json`.
- **Knowledge:** `knowledge/graph_nodes.jsonl`, `knowledge/graph_edges.jsonl`, `knowledge/graph_index.sqlite`.
- **Memory:** `memory/facts.jsonl`, `memory/summaries.json`.
- **Context:** `context/context_bundle.json`, `context/chunks/`, `context/vector.index`.
- **Reports:** `reports/*.md`, `reports/*.json`.
- **Cache:** `cache/parsed/`, `cache/extracted/` keyed by content hash.
- **Logs:** `logs/analysis.log` (rotated), `logs/audit.log`.

## Atomicity & Consistency
- Atomic writes: write to a temporary file in the same directory, then rename.
- Manifest is updated last; readers check the manifest version.
- SQLite transactions are used for index updates.
- Cache entries keyed by content hash are immutable and never modified.

## Caching
- Parsed models are cached by content hash to avoid re-parsing unchanged files.
- Extracted units are cached by `(sourceFingerprint, extractorVersion)` hash.
- Cache eviction uses LRU with configurable TTL and size limits.

## Retention
- `workspace.json` references current artifacts; unreferenced artifacts can be garbage-collected.
- `akwb clean` removes cache and artifacts.
- Logs are rotated by size and count.

## Inputs
- Domain entities and artifacts.
- Configuration (storage backend, cache limits, retention).

## Outputs
- Persisted workspace files.
- Cache hit/miss metrics.
- Storage diagnostics.

## Dependencies
- `04_DOMAIN_MODEL.md`
- `09_WORKSPACE_ENGINE.md`
- `11_DATA_MODEL.md`

## Future Extensions
- Remote object storage backends.
- Encrypted storage.
- Workspace compression and archiving.
- Shared workspace server.

## Risks
- Partial writes could corrupt the workspace; atomic rename mitigates this on local filesystems.
- Cache can grow unbounded; retention policy is required.
- Remote storage adds latency and failure modes.

## Design Decisions

- Storage backends implement repository interfaces defined in the domain layer.
- Workspace writes use a staging directory inside `.akwb/` and are promoted atomically via `workspace.json` updates.
- A transaction journal (`logs/transaction.log`) records every manifest change for crash recovery and rollback.
- Recovery logic replays the journal and removes orphaned artifact files on startup.
- Backup/restore is supported by copying `.akwb/`; the manifest references files by relative paths.
- Local-first, project-owned storage by default.
- Content-addressable cache makes incremental processing safe and fast.
- JSONL + SQLite hybrid balances streaming and queryability.
