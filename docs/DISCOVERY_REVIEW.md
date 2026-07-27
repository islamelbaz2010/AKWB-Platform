# Discovery Foundation Review

Review performed against: accuracy, performance, memory usage, cross-platform compatibility, incremental algorithm, fingerprint stability, ignore rules, and repository scalability.

## 1. Software Architect Review

### Strengths
- Clean separation between scanner, classifier, fingerprint, metadata, ignore, incremental, and registry components.
- Discovery engine is wired through the DI container and exposed as `akwb discover`.
- Artifact registry is a Pydantic model with stable IDs and JSON persistence.
- Incremental detector produces meaningful change sets: added, modified, deleted, renamed, unchanged.

### Issues Found & Fixed
- **Ignore pattern semantics**: original `fnmatch` matched full relative paths, causing anchored patterns like `/*.log` to ignore nested `.log` files.
  - *Fix*: rewrote `IgnoreEngine._matches` to match against path components, honoring leading `/` as root-anchored and trailing `/` as directory-only.
- **Workspace self-scanning**: the `.akwb` workspace could be discovered and written into the registry.
  - *Fix*: `.akwb` added to default ignores and `DiscoveryEngine` also injects the configured `workspace_dir` into ignore patterns.
- **Registry load project root**: `ArtifactRegistry.load()` defaulted to the storage root (workspace dir) when no registry existed.
  - *Fix*: load now infers the project root as `storage.root().parent`.
- **Per-artifact event overhead**: emitting `ArtifactDiscovered` for every artifact added measurable overhead in large repositories.
  - *Fix*: removed per-artifact event publication; only `DiscoveryCompleted` is emitted.

### Design Decisions
- Stable IDs are derived from `sha256(relative_path)` truncated to 32 hex chars, guaranteeing a stable 128-bit ID per path.
- Content hashes are computed separately and only once per path per scan.
- Incremental detection is hash-driven with size fallback for oversized files whose hash is skipped.

## 2. Performance Engineer Review

### Issues Found & Fixed
- **Double stat calls**: `FingerprintEngine.hash_file` and `MetadataExtractor.extract` each called `stat()`.
  - *Fix*: `DiscoveryEngine` now computes `stat` once per artifact and passes it to both engines. Both engines accept an optional `stat` argument.
- **Unchanged file re-hashing**: every scan re-read every file, making incremental scans nearly as slow as full scans.
  - *Fix*: `DiscoveryEngine` builds a `previous_by_path` lookup and reuses the prior hash when file size and mtime are unchanged.
- **Small hash read chunks**: reading files in 8 KiB blocks is suboptimal for modern filesystems.
  - *Fix*: increased chunk size to 64 KiB.
- **os.walk overhead**: `os.walk` yields strings and re-resolves paths.
  - *Fix*: `RecursiveScanner` now uses `os.scandir` directly, which returns `DirEntry` objects and avoids extra stat calls.

### Remaining Performance Notes
- The registry is still fully materialized in memory before JSON serialization. For very large repositories (hundreds of thousands of artifacts), memory will scale linearly with artifact count. Future work can stream registry output or switch to JSONL/SQLite.
- `Path.resolve()` is called per artifact. It is cheap but not free; benchmarks show acceptable results for the current scope.

## 3. File System Engineer Review

### Issues Found & Fixed
- **Symlink handling ambiguity**: `os.walk` with `followlinks` does not detect cycles and its symlink semantics are hard to tune.
  - *Fix*: custom `RecursiveScanner` with explicit control:
    - `follow_symlinks=False`: file symlinks skipped; directory symlinks yielded as directories but not descended into.
    - `follow_symlinks=True`: symlinks followed and `(dev, ino)` tracked to prevent infinite recursion.
- **Ignore engine resolving symlinks**: `path.resolve()` caused symlink paths to be evaluated against their target, losing the symlink name and allowing an ignored target to incorrectly influence the symlink path.
  - *Fix*: `IgnoreEngine` now uses `os.path.abspath` to normalize without resolving symlinks.
- **Cross-platform creation timestamp**: `st_ctime` means "metadata change" on Unix, not creation time.
  - *Fix*: `MetadataExtractor` uses `st_birthtime` when available (macOS/Windows) and falls back to `st_ctime`.
- **Hidden dot-file extension**: files like `.gitignore` were reported with extension `gitignore`.
  - *Fix*: dot-files without a real extension are reported with an empty extension string.

### Cycle Safety
- When `follow_symlinks=True`, the scanner tracks visited `(st_dev, st_ino)` pairs to avoid loops and duplicate traversal.

## 4. Incremental Algorithm Review

### Issues Found & Fixed
- **O(N*M) rename detection**: the original loop scanned all previous artifacts for each new artifact.
  - *Fix*: previous artifacts whose paths have disappeared are indexed by hash (and by size for oversized files with no hash). Lookup is O(1) on average.
- **Weak content equality for skipped hashes**: if `max_file_size_bytes` caused a hash to be skipped, any two skipped files compared equal.
  - *Fix*: `_content_equal` now compares size when both artifacts have no hash.
- **Rename candidate reuse**: a single previous artifact could be reused for multiple new artifacts.
  - *Fix*: matched previous IDs are tracked in `used_previous`.

### Correctness
- Added = new relative path not in previous.
- Modified = same relative path but content (hash/size) differs.
- Renamed = new relative path whose content matches a missing previous path.
- Deleted = previous path no longer present and not consumed by a rename.
- Unchanged = same relative path and same content.

## 5. Fingerprint Stability Review

- **Stable IDs**: deterministic, based on relative path only. Renaming an artifact produces a new ID. This is intentional: the ID is the canonical identity of the artifact *at that path*.
- **Content hashes**: default SHA-256, configurable via `discovery.hash_algorithm`. Reuse of previous hashes is based on size + mtime, so hash stability is preserved across scans for unchanged files.
- **ID collision probability**: 32 hex chars = 128 bits. Collision probability is negligible for project-scale artifact counts.

## 6. Ignore Rules Review

- Default ignore list covers common build/cache/dependency directories: `.git`, `node_modules`, `dist`, `build`, `coverage`, `.next`, `.cache`, `vendor`, `venv`, `.venv`, `target`, `__pycache__`, `.akwb`.
- Project-specific patterns are read from `.akwbignore` (comments and blank lines supported).
- Anchored (`/`), unanchored, directory-only (`/`), and glob (`*`, `?`) patterns are supported at the component level.

## 7. Scalability Review

- Current design supports tens of thousands of artifacts comfortably on a workstation (see `DISCOVERY_BENCHMARK.md`).
- The main scalability limit is in-memory registry materialization before serialization. This is acceptable for Sprint 2 and documented for future work.

## Summary of Changes Applied

| File | Change |
|---|---|
| `src/akwb/discovery/ignore.py` | Component-based gitignore-style matching, symlink-safe path normalization, directory-only patterns. |
| `src/akwb/discovery/scanner.py` | `os.scandir` traversal, explicit symlink handling, cycle detection. |
| `src/akwb/discovery/fingerprint.py` | Optional `stat` arg, 64 KiB read chunks. |
| `src/akwb/discovery/metadata.py` | Optional `stat` arg, birthtime fallback, hidden-file extension fix. |
| `src/akwb/discovery/incremental.py` | Hash/size index for O(1) rename detection, size fallback for skipped hashes. |
| `src/akwb/discovery/models.py` | Removed unused id index to save memory, fixed `load()` root inference. |
| `src/akwb/discovery/engine.py` | Reuses previous hashes, passes `stat`, removes per-artifact events. |
| `src/akwb/config.py` | `.akwb` added to default ignore list. |

## Recommendations
- Ready for production use within the sprint scope.
- Future work: streaming registry persistence, plugin-based detectors, and parallel directory traversal for very large repositories.
