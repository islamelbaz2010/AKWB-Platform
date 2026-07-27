# AKWB MVP Acceptance Test

**Status:** Official MVP acceptance criteria  
**Goal:** Define the exact scenario that proves AKWB is a usable Enterprise
Knowledge Compiler.

This test is the definition of done for Sprint 7. It is not a unit test; it is
a product-level acceptance scenario.

---

## Environment

- Fresh clone/install of AKWB.
- Python 3.12 or later.
- No pre-existing `.akwb/` workspace.
- No network access required.

## Test Commands

```bash
pip install -e .
cd /tmp/sample_project
akwb init .
akwb analyze .
```

## Sample Project

Create the following project before running the test:

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

### README.md

```markdown
# Sample Project

This project is used to validate the AKWB MVP.

## Decision

We will use PostgreSQL for persistence.

## Requirements

- The system must be observable.
- The system must be testable.
```

### docs/architecture.md

```markdown
# Architecture

## Component: API Server

The API server handles HTTP requests.

## Component: Database

PostgreSQL stores persistent data.
```

### src/config.py

```python
"""Configuration module."""

DATABASE_DSN = "postgresql://localhost/app"
```

### src/app.py

```python
"""Application module."""

from . import config


def connect():
    """Connect to the database."""
    return config.DATABASE_DSN
```

### src/__init__.py

```python
"""Sample package."""
```

### tests/test_app.py

```python
"""Tests for app."""


def test_connect():
    from sample_project.app import connect
    assert "postgresql" in connect()
```

---

## Expected CLI Behavior

### `akwb init .`

- Exit code: `0`
- Non-JSON output contains: `Workspace initialized at .akwb`
- Creates `.akwb/` with `workspace.json`, `logs/`, `cache/`, `staging/`.

### `akwb analyze .`

- Exit code: `0`
- Non-JSON output contains:
  - `Analyzed N artifacts`
  - `Knowledge objects: X`
  - `Knowledge relationships: Y`
- JSON output (when `--json` is used) contains:
  - `ok: true`
  - `artifact_count`
  - `object_count`
  - `relationship_count`
  - `diagnostics` (may be empty)

---

## Expected `.akwb/` Structure

```
.akwb/
├── workspace.json
├── index/
│   └── source_catalog.jsonl
├── knowledge/
│   ├── catalog.jsonl
│   ├── graph_nodes.jsonl
│   └── graph_edges.jsonl
├── graph/
│   ├── graph.jsonl
│   ├── graph.dot
│   └── graph.cypher
├── reports/
│   ├── summary.md
│   └── summary.json
└── logs/
    └── analysis.log
```

### Artifact files must be non-empty

- `index/source_catalog.jsonl` contains one line per discovered artifact.
- `knowledge/graph_nodes.jsonl` contains at least one node.
- `knowledge/graph_edges.jsonl` contains at least one edge.
- `graph/graph.dot` contains a `digraph` block.
- `graph/graph.cypher` contains at least one `CREATE` or `MERGE` statement.
- `reports/summary.md` contains the analysis summary.
- `reports/summary.json` is valid JSON.

---

## Expected Knowledge Objects

After `akwb analyze`, the workspace must contain at least:

| Object Type | Source File | Evidence |
|---|---|---|
| `document` | `README.md` | Extracted from Markdown content. |
| `decision` | `README.md` | Heading "Decision to use PostgreSQL". |
| `requirement` | `README.md` | List items under "Requirements". |
| `component` or `function` | `src/app.py` | Function `connect`. |
| `component` or `module` | `src/config.py` | Module or constant `DATABASE_DSN`. |
| `component` | `docs/architecture.md` | Heading "Component: API Server". |

At least **5** knowledge objects total.

---

## Expected Knowledge Relationships

The graph must contain at least:

| Relationship | Source | Target | Evidence |
|---|---|---|---|
| `contains` | `README.md` | decision object | The decision was extracted from the file. |
| `contains` | `src/app.py` | function object | The function was extracted from the file. |
| `contains` | `src/config.py` | component/constant object | The constant was extracted from the file. |
| `depends_on` or `references` | `src/app.py` | `src/config.py` | Import `from . import config`. |

At least **4** edges total.

---

## Expected Report Contents

### `reports/summary.md`

```markdown
# AKWB Analysis Summary

- Project: sample_project
- Artifacts analyzed: 6
- Knowledge objects: 7
- Knowledge relationships: 4
- Graph density: 0.XX
```

### `reports/summary.json`

```json
{
  "ok": true,
  "project_root": "/tmp/sample_project",
  "artifact_count": 6,
  "object_count": 7,
  "relationship_count": 4,
  "diagnostics": []
}
```

---

## Failure Criteria

The test fails if any of the following occur:

1. `akwb init` or `akwb analyze` exit with a non-zero code on the sample project.
2. Any expected file is missing from `.akwb/`.
3. `graph_nodes.jsonl` is empty.
4. `graph_edges.jsonl` is empty.
5. Fewer than 5 knowledge objects are produced.
6. Fewer than 4 relationships are produced.
7. Downstream products cannot read `.akwb/` artifacts without importing AKWB
   internals.

---

## Sign-Off

This acceptance test is the official definition of MVP completion. It must be
executed and passed before any Sprint 7 work is considered complete.
