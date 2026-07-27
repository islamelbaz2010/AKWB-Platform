# AKWB Known Issues — Version 1.0.0 MVP

This document lists issues discovered during the Release Readiness Review for
AKWB 1.0.0 MVP. Issues are grouped by area and tagged with severity:
**blocker**, **high**, **medium**, or **low**.

## Legend

- **Blocker** — must be resolved before the 1.0.0 MVP tag.
- **High** — significantly impacts correctness, security, or documentation
  accuracy; should be resolved before stable use.
- **Medium** — creates friction or misleading expectations; should be
  addressed soon after release.
- **Low** — polish or minor drift; acceptable to defer.

---

## Packaging & Metadata

### PKG-1: Missing root `README.md`
- **Severity:** medium
- **Location:** repository root; `pyproject.toml` line 9 (`readme = "README.md"`)
- **Description:** The package metadata references a `README.md` that does not
  exist. Source distributions and package indexes may show missing long
  description.
- **Workaround:** Add a `README.md` before building distributions.

### PKG-2: Version strings still read `0.1.0`
- **Severity:** high
- **Location:** `src/akwb/_version.py`, `pyproject.toml`, `workspace.json`
- **Description:** The release being reviewed is intended as `1.0.0` MVP, but
  source files and the produced workspace manifest still report `0.1.0`.
- **Workaround:** Bump `VERSION` and `pyproject.toml` `version` before tagging.

### PKG-3: Development classifier says "Alpha"
- **Severity:** low
- **Location:** `pyproject.toml` classifiers
- **Description:** `Development Status :: 3 - Alpha` does not match a 1.0.0
  stable intent.

---

## CLI

### CLI-1: `akwb init` does not create a project config file
- **Severity:** medium
- **Location:** `src/akwb/workspace/bootstrap.py::WorkspaceBootstrap.init`
- **Description:** `docs/13_CLI_SPECIFICATION.md` states that `akwb init`
  bootstraps `.akwb/config.yaml` and recommended `.gitignore` entries. The
  current implementation creates `workspace.json`, `logs/`, `cache/`, and
  `staging/` only.
- **Workaround:** Users can create `akwb.yaml` or `.akwb/config.yaml` manually.

### CLI-2: Many spec commands are not implemented
- **Severity:** medium
- **Location:** `src/akwb/cli.py`
- **Description:** The following commands from `docs/13_CLI_SPECIFICATION.md`
  are not present: `update`, `status`, `config`, `plugin`, `clean`, `ask`,
  `ci`.
- **Workaround:** Use `akwb analyze` for updates and run plugin management
  manually for now.

### CLI-3: Many spec flags are not implemented
- **Severity:** low
- **Location:** `src/akwb/cli.py` command definitions
- **Description:** Flags `--config`, `--plugin`, `--no-ai`, `--output`,
  `--format`, `--quiet`, `--verbose`, `--check` are documented but not
  implemented. `--output` is implemented only for `report` and `export`.

### CLI-4: `discover` default behavior includes directories as artifacts
- **Severity:** low
- **Location:** `src/akwb/discovery/engine.py` (uses
  `include_directories=True`)
- **Description:** The sample project produces 9 artifacts instead of the 6
  files expected by `docs/MVP_ACCEPTANCE_TEST.md`, because directories are
  counted. This does not fail the acceptance criteria but differs from the
  example summary.
- **Workaround:** Set `discovery.include_directories = false` in config or
  filter directories when consuming the catalog.

---

## Security

### SEC-1: Plugin sandboxing is not enforced
- **Severity:** high
- **Location:** `src/akwb/plugins/loader.py::PluginLoader._load_module_from_file`
- **Description:** Plugins are loaded by direct `exec_module()`. There is no
  permission enforcement, process isolation, or sandbox beyond the filesystem
  path validation in `LocalStorageBackend`.
- **Workaround:** Only load plugins from trusted local directories.

### SEC-2: No plugin signature verification
- **Severity:** high
- **Location:** `src/akwb/plugins/loader.py`, `src/akwb/plugins/registry.py`
- **Description:** `docs/16_SECURITY_MODEL.md` requires signing for plugins
  requesting `network` or from remote registries; no signature checks exist.
- **Workaround:** Only install plugins from trusted local sources.

### SEC-3: No secret scanning or redaction
- **Severity:** medium
- **Location:** discovery / extraction / report generation
- **Description:** No built-in secret scanner runs before artifacts are
  written to `.akwb/`. Tokens or credentials in source files may be copied into
  reports and graph exports.
- **Workaround:** Audit source content before analysis in untrusted projects.

### SEC-4: No audit log
- **Severity:** medium
- **Location:** workspace persistence
- **Description:** `docs/16_SECURITY_MODEL.md` specifies an append-only
  `logs/audit.log` for plugin load, network, execute, config change, and
  security events. Only `logs/analysis.log` is written.

### SEC-5: Security config fields are not enforced
- **Severity:** medium
- **Location:** `src/akwb/config.py::Config` (no `security` section implemented)
- **Description:** `docs/12_CONFIGURATION.md` lists `security.allowNetwork`,
  `allowExecute`, `secretScanning`, and `pluginSignatureRequired`, but these
  settings are not wired into the CLI or engine.

---

## Performance

### PERF-1: No streaming for large catalogs
- **Severity:** medium
- **Location:** `src/akwb/knowledge/serialization.py::JsonlSerializer`
- **Description:** The JSONL serializer materializes the entire catalog as a
  single string. Large repositories will consume memory proportional to
  catalog size.

### PERF-2: Graph writes build full in-memory buffers
- **Severity:** medium
- **Location:** `src/akwb/graph/storage.py::_write_jsonl`, `_write_nodes_jsonl`,
  `_write_edges_jsonl`
- **Description:** All graph records are accumulated in a Python list and
  joined before writing. For large graphs this can spike memory.

### PERF-3: No concurrency or process pools
- **Severity:** medium
- **Location:** `src/akwb/analysis/engine.py`
- **Description:** Files are processed sequentially. The performance targets
  in `docs/17_PERFORMANCE_STRATEGY.md` (1M LOC in <5 min, <4 GB) are unlikely
  to be met without parallelization and caching.

### PERF-4: No benchmark suite run
- **Severity:** low
- **Location:** `tests/`
- **Description:** No performance or regression tests were executed for this
  review. Claims about large-project support are unverified.

---

## Graph & Extraction

### GRAPH-1: No relationship inference beyond imports
- **Severity:** low
- **Location:** `src/akwb/analysis/engine.py`
- **Description:** Only explicit `contains` relationships and Python import
  `depends_on` are extracted. Semantic relationships (e.g., a requirement
  referencing a component) are not inferred.

### EXTRACT-1: Python extraction only handles top-level nodes
- **Severity:** low
- **Location:** `src/akwb/extraction/python.py`
- **Description:** Nested functions, class methods beyond first-level, type
  aliases, and async context managers are not extracted. Docstrings are not
  attached as descriptions.

### EXTRACT-2: Markdown extraction is rule-based
- **Severity:** low
- **Location:** `src/akwb/extraction/extractors.py`, `src/akwb/extraction/markdown.py`
- **Description:** Extraction uses regex/heading heuristics, not a rich AST
  parser. Nested structures and non-Latin scripts may be mis-segmented.

---

## Code Quality

### QUAL-1: `mypy` reports 32 errors
- **Severity:** medium
- **Location:** 13 source files, notably `src/akwb/cli.py` and
  `src/akwb/analysis/engine.py`
- **Description:** Missing stub packages, untyped parameters, and real type
  mismatches remain. The project claims `mypy --strict` as a target in
  `docs/IMPLEMENTATION_GUIDE.md`.

### QUAL-2: `ruff` reports 64 findings
- **Severity:** low
- **Location:** `src/` and `tests/`
- **Description:** Most are auto-fixable style suggestions, but 64 issues
  indicate the code has not been lint-cleaned for a stable release.

### QUAL-3: Broad `except Exception` in hot paths
- **Severity:** low
- **Location:** `src/akwb/analysis/engine.py`, `src/akwb/extraction/pipeline.py`
- **Description:** Errors are caught and recorded as diagnostics, which is
  good for resilience, but some exceptions may hide real bugs from users.

---

## Documentation

### DOCS-1: Implementation guide layout is out of sync
- **Severity:** medium
- **Location:** `docs/IMPLEMENTATION_GUIDE.md` Section 3
- **Description:** The guide describes a directory structure with
  `akwb/cli/`, `akwb/domain/`, `akwb/engines/`, etc. that does not match the
  current source tree.

### DOCS-2: Security / performance docs describe future features as present
- **Severity:** low
- **Location:** `docs/16_SECURITY_MODEL.md`, `docs/17_PERFORMANCE_STRATEGY.md`
- **Description:** These documents describe capabilities that are not
  implemented (sandboxing, audit log, streaming, process pools) without
  explicit "future" or "not yet implemented" markers.

### DOCS-3: No root quickstart
- **Severity:** medium
- **Location:** repository root
- **Description:** A new user has no `README.md` or `CONTRIBUTING.md` to
  orient them. `docs/` is comprehensive but not entry-level.

---

## Issue Tally by Severity

| Severity | Count |
|---|---|
| Blocker | 0 |
| High | 3 |
| Medium | 12 |
| Low | 10 |

**Summary:** No blockers were identified. The high-severity issues are version
metadata and plugin security; these should be fixed or clearly documented
before the 1.0.0 MVP is published.
