# Incremental Analysis

## Purpose
Define how AKWB avoids full re-analysis by detecting changes, tracking dependencies, and invalidating only affected artifacts.

## Responsibilities
- Compute and compare file fingerprints.
- Maintain an artifact dependency graph.
- Determine the minimal work required for each analysis run.
- Support full re-analysis via `--force`.
- Ensure correctness of incremental updates.

## Inputs
- Current `SourceCatalog` and fingerprints.
- Previous `SourceCatalog` and fingerprints.
- Artifact manifest with source references.
- Knowledge graph dependency map.

## Concepts
- **Fingerprint:** `{algorithm, hash, size, mtime}`. Default algorithm is `sha256` of file content.
- **Change Set:** files added, removed, modified, or unchanged.
- **Invalidation Graph:** artifacts depend on source entries and knowledge units; when a source changes, all downstream artifacts are invalidated.
- **Snapshot:** immutable record of a complete analysis state.

## Process
1. **Catalog Diff:** Compare the new `SourceCatalog` with the previous one by relative path and fingerprint.
2. **Impact Propagation:** For modified or removed files, mark their knowledge units, relationships, and dependent artifacts as invalid.
3. **Selective Reprocessing:** Re-run discovery, parsing, and extraction only for changed or invalidated sources.
4. **Artifact Rebuild:** Rebuild invalidated artifacts; preserve unchanged artifacts.
5. **Manifest Update:** Write a new artifact manifest and snapshot reference.
6. **Full Rebuild:** `akwb analyze --force` ignores prior state.

## Correctness Rules
- Adding or removing a source invalidates its units and any relationships whose evidence spans changed files.
- Changes to a parser, extractor, or plugin version invalidate all outputs produced by that plugin.
- Configuration changes invalidate dependent artifacts.
- Renames are treated as an add and a remove; future rename detection can reduce churn.

## Outputs
- Updated `SourceCatalog`.
- Change set.
- Invalidation list.
- New `Snapshot`.
- Rebuilt artifacts.

## Dependencies
- `04_DOMAIN_MODEL.md`
- `07_DISCOVERY_ENGINE.md`
- `08_KNOWLEDGE_ENGINE.md`
- `09_WORKSPACE_ENGINE.md`
- `11_DATA_MODEL.md`

## Future Extensions
- Fine-grained AST diff for smaller invalidation.
- Build-system integration for build artifacts.
- Distributed incremental cache.

## Risks
- Missing a transitive invalidation causes stale artifacts.
- Fingerprint collisions are extremely unlikely with `sha256` but still theoretically possible.
- Renames cause unnecessary reprocessing.

## Design Decisions

- Content-based fingerprints guarantee correctness; the fingerprint includes the plugin/extractor version for cache entries.
- The invalidation graph is stored in SQLite for queryability and tracks source → knowledge unit → artifact dependencies.
- Plugin version changes invalidate all artifacts produced by that plugin; core version changes invalidate the entire workspace.
- Configuration changes invalidate artifacts whose inputs are affected (e.g., `extractionDepth` changes invalidate the knowledge graph).
- Renames are initially treated as add+remove; a future rename-detector can produce `RenameDetected` events to reduce churn.
- Snapshots are immutable; the workspace references the current snapshot and can reference a small history for rollback.
- Full analysis is always available with `--force`.
