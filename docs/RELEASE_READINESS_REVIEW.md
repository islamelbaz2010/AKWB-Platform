# AKWB Release Readiness Review

## Executive Summary

This review evaluates the AKWB repository for a **Version 1.0.0 MVP** release. The
MVP acceptance scenario (`pip install -e .`, `akwb init .`, `akwb analyze .` on
the canonical sample project) passes cleanly, all automated tests pass, and the
primary workspace artifacts are produced as specified. However, the package
metadata still advertises version `0.1.0`, the repository is missing a top-level
`README.md`, the CLI does not implement every command/flag documented in the CLI
specification, and the security/performance model is only partially realized.

**Overall verdict:** **READY WITH MINOR ISSUES** for a Version 1.0.0 MVP tag,
provided the packaging/metadata items called out below are resolved first.

## Scope & Methodology

- **Version reviewed:** `0.1.0` (source-of-truth in `src/akwb/_version.py` and
  `pyproject.toml`).
- **Target release:** `1.0.0` MVP.
- **Test environment:** macOS, Python 3.14.4, fresh `venv` at `/tmp/akwb_venv`.
- **Commands exercised:** `pip install -e .`, `akwb init`, `akwb analyze`,
  `akwb discover`, `akwb doctor`, `akwb report`, `akwb export`, `akwb version`.
- **Static checks:** `pytest -q`, `ruff check src tests`, `mypy src`.
- **Acceptance test:** `docs/MVP_ACCEPTANCE_TEST.md` sample project structure.

## Installation & First-Run Experience

### Packaging

- `pip install -e .` completes successfully and installs the `akwb` console script.
- `pyproject.toml` is well-formed, declares the correct `project.scripts` entry
  point, and pins Python `>=3.12`.
- **Issue:** `pyproject.toml` sets `readme = "README.md"`, but `README.md` does
  not exist at the repository root. This produces incomplete package metadata and
  may break source distribution builds on some packaging tools.
- **Issue:** The classifier `Development Status :: 3 - Alpha` and the version
  string `0.1.0` do not reflect a 1.0.0 MVP / stable intent.

### First Run

- `akwb init . --force` initializes `.akwb/` with `workspace.json`, `logs/`,
  `cache/`, and `staging/`.
- `akwb analyze .` exits `0` and prints:

```text
Analyzed 9 artifacts
Knowledge objects: 20
Knowledge relationships: 16
Workspace written to .../.akwb
```

- JSON mode (`akwb analyze . --json`) emits valid JSON with the documented
  fields (`ok`, `artifact_count`, `object_count`, `relationship_count`,
  `graph_density`, `diagnostics`).
- `akwb analyze` auto-initializes a workspace when none exists, so a new user can
  run a single command and get output.

## Workspace Quality

The `.akwb/` workspace produced for the sample project contains the expected
files and they are non-empty:

| Artifact | Size / Lines | Notes |
|---|---|---|
| `workspace.json` | 1 | Schema `workspace-v1`, `akwb_version` `0.1.0` |
| `index/source_catalog.jsonl` | 9 | One line per discovered artifact |
| `knowledge/catalog.jsonl` | 88 | Full catalog + framework types |
| `knowledge/graph_nodes.jsonl` | 20 | Nodes matching object count |
| `knowledge/graph_edges.jsonl` | 16 | Edges matching relationship count |
| `graph/graph.jsonl` | combined | `metadata`, `GraphNode`, `GraphEdge` records |
| `graph/graph.dot` | 38 | Valid `digraph G { ... }` block |
| `graph/graph.cypher` | 36 | `MERGE`/`MATCH` statements |
| `reports/summary.md` | 19 | Markdown summary with node/edge type breakdown |
| `reports/summary.json` | valid JSON | `ok`, counts, density, diagnostics |
| `logs/analysis.log` | non-empty | Diagnostics written as text |

### Observations

- The catalog and graph outputs are valid JSONL and DOT/Cypher.
- `reports/summary.json` matches the schema documented in the acceptance test.
- `graph/graph.dot` renders correctly and includes a `depends_on` edge from
  `src/app.py` to `src/config.py`.
- The workspace manifest lists all generated artifacts.

## CLI Experience

### Implemented commands

| Command | Status | Notes |
|---|---|---|
| `akwb version` | Works | Prints `0.1.0` |
| `akwb init [path]` | Works | `--force`, `--json` supported |
| `akwb analyze [path]` | Works | `--force`, `--depth`, `--json` supported |
| `akwb discover` | Works | `--json` supported |
| `akwb doctor` | Works | `--json` supported |
| `akwb report {summary\|structure\|graph}` | Works | `--output` supported |
| `akwb export {jsonl\|dot\|cypher}` | Works | `--output` supported |

### Error handling & exit codes

- `akwb init /nonexistent` prints a clear error and exits `1`.
- `akwb init` against an existing workspace exits `1` with a helpful `--force`
  suggestion.
- `akwb analyze /nonexistent` exits `2`.
- `akwb report` or `akwb export` without a workspace exits `1`.
- Invalid `export` format is rejected by Click with usage help.
- `doctor` on a valid project exits `0` and reports Python version, project-root
  writability, workspace existence, and `workspace.json` readability.

### Gaps relative to the CLI specification

`docs/13_CLI_SPECIFICATION.md` describes a broader surface than what is
implemented:

- Missing commands: `akwb update`, `akwb status`, `akwb config`, `akwb plugin`,
  `akwb clean`, `akwb ask`, `akwb ci`.
- Missing flags: `--config`, `--plugin`, `--no-ai`, `--output`, `--format`,
  `--quiet`, `--verbose`, `--check`.
- The `discover` `--json` output is functional but not schema-versioned as
  described.

These are non-blocking for the MVP but create documentation drift.

## Documentation Completeness for New Developers

### Strengths

- The `docs/` directory is extensive (75 files) and covers product vision,
  requirements, architecture, domain model, plugins, discovery, extraction,
  graph engine, configuration, security, performance, testing, and release
  strategy.
- `docs/MVP_ACCEPTANCE_TEST.md` is the clear, executable definition of done for
  this release.
- `docs/IMPLEMENTATION_GUIDE.md` documents conventions (Python 3.12, typing,
  clean architecture, dependency injection, testing).

### Gaps

- **No top-level `README.md`:** A new contributor cannot learn how to install,
  run, or test the project from the repository root.
- **No `CONTRIBUTING.md` or `CHANGELOG.md`.**
- `IMPLEMENTATION_GUIDE.md` shows a repository layout (`akwb/cli/`,
  `akwb/domain/`, `akwb/engines/`, etc.) that does not match the current
  `src/akwb/` structure. This is confusing for new developers.
- Several design documents (`SECURITY_MODEL.md`, `PERFORMANCE_STRATEGY.md`,
  `CLI_SPECIFICATION.md`) describe capabilities that are not yet implemented,
  without clearly marking them as future work.

## Performance

- No performance or benchmark tests were run as part of this review.
- The implementation is single-threaded and reads entire files into memory. The
  graph and catalog serializers build full in-memory string buffers before
  writing, which does not meet the streaming/1M-LOC targets in
  `docs/17_PERFORMANCE_STRATEGY.md`.
- For the MVP sample project the runtime is effectively instantaneous, but the
  current implementation is not production-grade for large repositories.

## Security

### Implemented

- Analysis is local by default; telemetry is disabled (`telemetry_enabled:
  false`).
- `LocalStorageBackend._resolve()` uses `Path.is_relative_to()` to enforce that
  all workspace writes stay inside `.akwb/`.
- Plugin loading is opt-in via `plugins.directories`; the default list is empty.

### Not implemented / gaps

- **Plugin sandboxing:** `PluginLoader` executes arbitrary Python modules with
  `exec_module()` and does not enforce declared permissions.
- **Signature verification:** No Sigstore/cosign/minisign checks for remote or
  elevated plugins.
- **Secret scanning/redaction:** No built-in scanner; no redaction in artifacts.
- **Audit log:** `logs/audit.log` is not produced.
- **Resource watchdog:** No CPU, memory, or file-size enforcement beyond config
  defaults.
- **Network/execute gates:** `Config.security.allowNetwork` and `allowExecute`
  exist as schema fields but are not checked before plugin execution.

These gaps are acceptable for an offline, local-first MVP, but they must be
prominently disclosed and tracked for post-MVP work.

## Backward Compatibility

- This is the first public release; there is no prior version to be compatible
  with.
- The workspace format is versioned as `workspace-v1` in `workspace.json`.
- **Action required:** Before tagging `1.0.0`, bump `VERSION` in
  `src/akwb/_version.py` and `version` in `pyproject.toml`.
- No migration tooling is needed for this release.

## Technical Debt

- `mypy src` reports **32 errors across 13 files**. Many are missing stub
  packages (yaml), untyped parameters, and generic type arguments; some are real
  type mismatches in `src/akwb/cli.py` and `src/akwb/analysis/engine.py`.
- `ruff check src tests` reports **64 findings**. Most are style/lint
  suggestions (e.g., `RUF015`) and 36 are auto-fixable, but they indicate the
  code has not been fully lint-cleaned for a stable release.
- `src/akwb/cli.py` contains exit-code branching that is mostly correct but
  mixes some `bool`/`int`/`str` typed values into a single `output` dict,
  contributing to mypy noise.
- `src/akwb/extraction/python.py` and `src/akwb/analysis/engine.py` rely on
  broad `except Exception` handlers. While appropriate for a pipeline that must
  continue on partial failure, the diagnostics surfaced are not always
  user-actionable.

## Recommendations

1. **Packaging:** Add `README.md`, bump version strings to `1.0.0`, update the
   `Development Status` classifier.
2. **Docs:** Add a root quickstart, reconcile `IMPLEMENTATION_GUIDE.md` with the
   actual source tree, and mark unimplemented CLI/security features as
   "post-MVP".
3. **Static analysis:** Fix the subset of mypy/ruff issues that represent real
   type or lint problems before stable release.
4. **Security:** Document the current security posture and the fact that plugin
   sandboxing/signature verification is not yet enforced.
5. **Performance:** Before claiming large-repository support, implement
   streaming JSONL serialization and run the benchmark suite described in
   `docs/17_PERFORMANCE_STRATEGY.md`.
6. **CLI:** Decide whether the missing commands in `CLI_SPECIFICATION.md` are
   in-scope for 1.0.0 or should be deferred and the spec updated.

## Acceptance Test Result

| Criterion | Result |
|---|---|
| `pip install -e .` succeeds | PASS |
| `akwb init .` exits `0` | PASS |
| `akwb analyze .` exits `0` | PASS |
| `.akwb/` workspace structure matches spec | PASS |
| All required artifact files non-empty | PASS |
| Knowledge objects >= 5 | PASS (20 produced) |
| Knowledge relationships >= 4 | PASS (16 produced) |
| `depends_on` / `references` present | PASS |
| `reports/summary.md` and `summary.json` correct | PASS |
| `pytest` suite passes | PASS (100%) |

## Conclusion

AKWB satisfies the documented MVP acceptance criteria. The core end-to-end flow
is functional, the workspace artifacts are useful, and the test suite is green.
The remaining items are packaging hygiene, documentation alignment, and
post-MVP security/performance work. Addressing the **minor issues** listed above
before tagging is recommended, but none are release blockers for the 1.0.0 MVP.
