# Sprint 2 Report — Discovery Foundation

## Goal

Implement the AKWB Discovery Foundation. The CLI must be able to scan any project path and produce a canonical artifact registry, without extracting knowledge, generating workspace documents, or building AI context.

## What Was Delivered

| Component | Status | Notes |
|---|---|---|
| `DiscoveryConfig` | Done | Added to `akwb.config` with ignore patterns, symlink/hash/large-file settings, registry file name. |
| Ignore Engine | Done | `akwb/discovery/ignore.py` — default ignores + `.akwbignore` project patterns. |
| Fingerprint Engine | Done | `akwb/discovery/fingerprint.py` — streaming SHA-256 content hash and path-based stable IDs. |
| File Classifier | Done | `akwb/discovery/classifier.py` — extension/mime type mapping to AKWB artifact types and categories. |
| Metadata Extractor | Done | `akwb/discovery/metadata.py` — size, timestamps, parent directory, tags, status. |
| Artifact Registry | Done | `akwb/discovery/models.py` — Pydantic models, in-memory indexes, JSON persistence. |
| Recursive Scanner | Done | `akwb/discovery/scanner.py` — `os.walk` with directory pruning, optional symlink following. |
| Incremental Detection | Done | `akwb/discovery/incremental.py` — new / modified / deleted / renamed / unchanged statuses. |
| Discovery Engine | Done | `akwb/discovery/engine.py` — orchestrates scan, classify, fingerprint, metadata, incremental detection. |
| DI wiring | Done | `Container.discovery_engine` added. |
| CLI `discover` | Done | `akwb discover [--json]` added in `akwb/cli.py`. |
| Tests | Done | Unit + integration tests covering empty/small/large projects, nested folders, ignores, symlinks, duplicates, renamed/modified/deleted files. |
| Fixtures | Done | `fixtures/empty/` and `fixtures/small_project/` with varied file types and a `.akwbignore`. |

## What Was Explicitly Excluded

- Knowledge extraction
- Workspace document/report generation
- AI Context building
- Semantic parsing

## Test Results

```
$ python3 -m pytest -q
.....................................
47 passed in <1s
```

## CLI Smoke Test

```text
$ PYTHONPATH=src python3 -m akwb --project-root fixtures/small_project discover --json
Discovered 8 artifacts
```

The JSON output contains `id`, `absolute_path`, `relative_path`, `type`, `category`, `extension`, `hash`, `size`, `created_time`, `modified_time`, `parent_directory`, `tags`, `status`, and `previous_path` for each artifact.

## Implementation Notes

- Stable IDs are derived from the artifact's project-relative path (SHA-256), so the same path always receives the same ID across scans.
- Content hashes are computed separately for duplicate detection and incremental change tracking.
- The workspace directory (`.akwb`) is automatically excluded from discovery so the workspace does not scan itself.
- The default ignore list matches the sprint spec: `.git`, `node_modules`, `dist`, `build`, `coverage`, `.next`, `.cache`, `vendor`, `venv`, `.venv`, `target`, `__pycache__`.
- The `.akwbignore` file can add project-specific patterns such as `*.log`.
- Symlinks are skipped by default and optionally followed.
- Renamed files are detected by matching a newly appeared content hash against a missing previous path.

## Known Limitations / Next Sprint Inputs

- The classifier uses extension and MIME guessing; future sprints can integrate plugin-based detectors.
- The incremental detector does not yet handle directory-level change propagation.
- Large-file hashing is configurable but currently computes the full hash in chunks; an upper-size skip threshold is supported.
- The artifact registry is stored as JSON; a SQLite-backed registry can be added later if needed.

## Conclusion

The Discovery Foundation is complete and tested. `akwb discover` can inventory a project, respect ignores, classify artifacts, fingerprint contents, detect incremental changes, and persist a canonical registry. Ready for approval before proceeding to Sprint 3 (Knowledge Extraction / Workspace Generation as directed).
