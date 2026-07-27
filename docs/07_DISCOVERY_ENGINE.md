# Discovery Engine

## Purpose
Define how AKWB automatically scans a project, identifies knowledge sources, and classifies them with minimal or no manual configuration.

## Responsibilities
- Enumerate files within the project root.
- Detect project type and language/framework mix.
- Classify each source by language, role, and content type.
- Emit `SourceDiscovered` and `SourceClassified` events.
- Build the `SourceCatalog`.
- Honor ignore patterns, size limits, depth limits, and binary exclusions.

## Inputs
- Project root path.
- Configuration: ignore patterns, include patterns, max file size, max depth, follow symlinks, use `.gitignore`.
- Registered `Detector` plugins.
- Prior `SourceCatalog` and fingerprints (for incremental diff).

## Process
1. **Filesystem Walk:** Traverse the project root using configurable rules. Skip `.git`, `.akwb`, package-manager directories (`node_modules`, `vendor`, `target`, etc.), build artifacts, and user-defined ignore patterns.
2. **Fingerprinting:** Compute a content hash, size, and last-modified time for every discovered file. Use fast pre-hash checks to skip unchanged files.
3. **Detector Selection:** Run registered `Detector` plugins in priority order. Each detector returns a confidence score and classification hints.
4. **Classification:** Merge detector outputs into a final `SourceEntry`:
   - `language` (e.g., `python`, `javascript`, `markdown`, `unknown`)
   - `role` (e.g., `source`, `test`, `doc`, `config`, `ci`, `asset`)
   - `mimeType`, `tags`
   - `parserHint` (preferred parser plugin)
   - `encoding`
5. **Catalog Assembly:** Produce `SourceCatalog` with sorted entries and classification summaries.
6. **Event Emission:** Publish events for the incremental manager and downstream engines.

## Outputs
- `SourceCatalog` aggregate.
- `SourceEntry` entities.
- `SourceDiscovered` and `SourceClassified` domain events.
- Change set (added, removed, modified, unchanged) for the incremental engine.

## Dependencies
- `04_DOMAIN_MODEL.md`
- `06_PLUGIN_ARCHITECTURE.md`
- `14_INCREMENTAL_ANALYSIS.md`

## Future Extensions
- VCS history as a knowledge source (commit messages, authors, change frequency).
- Remote knowledge sources (URLs, issue trackers, package registries) via opt-in plugins.
- Multi-root workspaces for monorepos.
- Duplicate-file detection and deduplication.

## Risks
- Misclassification of polyglot or generated files.
- Performance degradation on repositories with large generated directories.
- Important files hidden by overly aggressive ignore patterns.

## Design Decisions

- Project root detection uses a ranked list of markers (`.git`, `pyproject.toml`, `package.json`, `pom.xml`, `go.mod`, `Cargo.toml`, etc.) and stops at the filesystem root if none are found.
- File encoding is detected with `charset-normalizer` or `chardet`; UTF-8 is assumed only when detection is ambiguous.
- Default ignore patterns include `.git`, `.akwb`, `node_modules`, `vendor`, `target`, `__pycache__`, `.pytest_cache`, `dist`, `build`, `.venv`, and common IDE directories.
- Filter precedence: explicit `includePatterns` > explicit `ignorePatterns` > `.gitignore` > built-in defaults.
- Dependency manifest files (`requirements.txt`, `package.json`, `pom.xml`, etc.) are classified as `config` but tagged for dependency extraction.
- Generated directories are identified by detector heuristics (e.g., `node_modules` contains a `.package-lock` sentinel) and skipped unless explicitly included.
- Detectors vote with confidence; the highest-confidence non-conflicting hints win.
- Ignore patterns follow `.gitignore` syntax plus `akwb`-specific configuration.
- Fingerprint uses `sha256` of content plus file size; mtime is used only for quick skip candidates.
- Binary files are excluded by default unless a detector explicitly claims and handles them.
