# Release Verification — AKWB 1.0.0 MVP

**Version under verification:** 1.0.0
**Date:** 2026-07-27
**Environment:** Python 3.12+ (verified on macOS, Python 3.14 during validation), editable install in a fresh virtual environment.

## Summary

| Gate | Tool / Test | Status | Evidence |
|---|---|---|---|
| Static typing | `mypy src` | PASS | `Success: no issues found in 63 source files` |
| Linting | `ruff check src tests` | PASS | `All checks passed!` |
| Unit & integration tests | `pytest -q` | PASS | 208 passed in 100% block |
| Quick start | Fresh venv install + `akwb analyze .` | PASS | `.akwb/` created with workspace artifacts |
| MVP acceptance test | `akwb init .` + `akwb analyze .` on `/tmp/akwb_acceptance` | PASS | See below |
| Version strings | `pyproject.toml`, `_version.py`, fixtures | PASS | All 0.1.0 → 1.0.0 |
| Docs alignment | CLI, Security, Performance, Implementation | PASS | POST-MVP / PLANNED annotations added |
| Release metadata | classifiers, keywords, URLs | PASS | Updated in `pyproject.toml` |
| README / final docs | README, CHANGELOG, CONTRIBUTING, ROADMAP, SUPPORT | PASS | Created at repository root |

## Static Analysis

### `ruff check src tests`

```
All checks passed!
```

All real issues were fixed; no suppressions were added for non-false-positives.

### `mypy src`

```
Success: no issues found in 63 source files
```

## Test Suite

```
........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
```

208 tests passed.

## Quick Start Validation

Fresh virtual environment created at `/tmp/akwb_release_venv`:

```bash
pip install -e ".[dev]"
mkdir /tmp/akwb_quickstart
# create README.md and src/app.py
akwb analyze .
```

Result:

```
INFO [akwb] Discovered 3 artifacts; added=0, modified=0, deleted=0, renamed=0
Analyzed 3 artifacts
Knowledge objects: 5
Knowledge relationships: 3
Workspace written to /private/tmp/akwb_quickstart/.akwb
```

Workspace files created:

```
.akwb/artifacts.json
.akwb/workspace.json
.akwb/index/source_catalog.jsonl
.akwb/knowledge/catalog.jsonl
.akwb/knowledge/graph.cypher
.akwb/knowledge/graph.dot
.akwb/knowledge/graph.jsonl
.akwb/knowledge/graph_edges.jsonl
.akwb/knowledge/graph_nodes.jsonl
.akwb/graph/graph.cypher
.akwb/graph/graph.dot
.akwb/graph/graph.jsonl
.akwb/graph/graph_edges.jsonl
.akwb/graph/graph_nodes.jsonl
.akwb/reports/summary.json
.akwb/reports/summary.md
.akwb/logs/analysis.log
```

## MVP Acceptance Test

Sample project created at `/tmp/akwb_acceptance` matching `docs/MVP_ACCEPTANCE_TEST.md`:

```
sample_project/
├── README.md
├── docs/
│   └── architecture.md
├── src/
│   ├── __init__.py
│   ├── app.py
│   └── config.py
└── tests/
    └── test_app.py
```

Execution:

```bash
akwb init .
akwb analyze .
```

JSON result:

```json
{
  "ok": true,
  "project_root": "/private/tmp/akwb_acceptance",
  "workspace_dir": "/private/tmp/akwb_acceptance/.akwb",
  "artifact_count": 9,
  "object_count": 20,
  "relationship_count": 16,
  "graph_density": 0.042105263157894736,
  "diagnostics": []
}
```

All required artifacts present:

- `graph_nodes.jsonl`: 20 nodes
- `graph_edges.jsonl`: 16 edges
- `catalog.jsonl`: 88 records
- `summary.md` and `summary.json` generated

The acceptance test passes all criteria in `docs/MVP_ACCEPTANCE_TEST.md`.

## Notable Fixes Since Last Review

- Added `os` import in `src/akwb/discovery/engine.py` for `stat_result` type annotations.
- Fixed `KnowledgeEvidence.source` nullability in `src/akwb/analysis/engine.py` by tracking the source object for each Python import.
- Added `SyntaxError`/`ValueError` handling in `src/akwb/analysis/engine.py` so malformed Python files do not crash the entire analysis.
- Resolved all `mypy` and `ruff` warnings across `src/` and `tests/`.

## Known Limitations (Documented, Not Blockers)

- Security hardening (sandboxing, signatures, audit logging, secret scanning) is documented as POST-MVP / PLANNED in `docs/16_SECURITY_MODEL.md`.
- Performance optimizations (concurrency, streaming, caches, SQLite spill) are documented as POST-MVP / PLANNED in `docs/17_PERFORMANCE_STRATEGY.md`.
- Several CLI commands (`update`, `status`, `config`, `plugin`, `clean`, `ask`, `ci`) are documented as POST-MVP / PLANNED in `docs/13_CLI_SPECIFICATION.md`.

## Conclusion

All release gates pass. The code is lint- and type-clean, the test suite is green, and the MVP acceptance scenario completes successfully on a fresh install.
