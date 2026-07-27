# AKWB Release Notes — Version 1.0.0 MVP

## Overview

This release delivers the Minimum Viable Engine (MVE) for the AKWB Platform: a
local-first, project-owned knowledge workspace that can discover artifacts,
extract knowledge from Markdown and Python source, build a knowledge graph, and
export it for downstream tools.

**Version:** 1.0.0  
**Status:** MVP (Minimum Viable Product)  
**Workspace format:** `workspace-v1`  
**Plugin API version:** `1`  
**Minimum Python:** `3.12`

## Installation

```bash
pip install akwb==1.0.0
```

Or install from source:

```bash
git clone <repository>
cd akwb-platform
pip install -e .
```

## Quick Start

```bash
mkdir my_project && cd my_project
# create some README.md and Python source files
akwb analyze .
# open .akwb/reports/summary.md and .akwb/graph/graph.dot
```

## What's New in 1.0.0

### End-to-end analysis pipeline

- `akwb analyze` discovers project artifacts, extracts knowledge, builds a
  knowledge graph, validates it, and writes the `.akwb/` workspace in one
  command.
- `akwb init` prepares a fresh `.akwb/` workspace with `workspace.json`,
  `logs/`, `cache/`, and `staging/`.
- `akwb analyze` auto-initializes the workspace when it is missing.

### CLI commands

- `akwb version` — print the CLI version.
- `akwb init [path]` — initialize the workspace.
- `akwb analyze [path]` — run the full analysis pipeline.
- `akwb discover` — scan and register project artifacts.
- `akwb doctor` — validate the environment and workspace.
- `akwb report {summary|structure|graph}` — display generated reports.
- `akwb export {jsonl|dot|cypher}` — export the graph to portable formats.

### Knowledge extraction

- Markdown/rule-based extraction of documents, decisions, goals, and
  requirements from headings and list items.
- Python AST parser producing `component` knowledge objects for top-level
  functions, classes, and assignments.
- Import resolution for `from . import X`, `from .module import X`, and
  absolute local imports, producing `depends_on` relationships.

### Knowledge graph

- In-memory `KnowledgeGraph` built from a validated `KnowledgeCatalog`.
- Graph exports to JSONL, GraphViz DOT, and Neo4j Cypher.
- Graph validation: broken references, directed cycles, duplicate edges,
  orphan nodes, and invalid relationship types.
- Statistics: node/edge counts, node type counts, edge type counts, density.

### Workspace artifacts

The `.akwb/` directory now produces:

- `workspace.json` — manifest and config snapshot.
- `index/source_catalog.jsonl` — discovered artifact registry.
- `knowledge/catalog.jsonl` — full knowledge catalog.
- `knowledge/graph_nodes.jsonl`, `knowledge/graph_edges.jsonl` — graph data.
- `graph/graph.jsonl`, `graph/graph.dot`, `graph/graph.cypher` — graph exports.
- `reports/summary.md`, `reports/summary.json` — analysis summary.
- `logs/analysis.log` — analysis diagnostics.

### Plugin framework

- `PluginLoader` and `PluginRegistry` support local plugin packages with a
  `plugin.yaml` manifest.
- `Container` wires the core engines via constructor injection.
- Plugin ports: `reader`, `segmenter`, `extractor`, `candidate_builder`,
  `candidate_validator`, `knowledge_type_provider`,
  `relationship_type_provider`, `evidence_type_provider`,
  `knowledge_validator_provider`, `graph_storage`, `graph_query_engine`,
  `graph_traversal`, `graph_index`.

### Configuration

- `Config` and `ConfigLoader` merge built-in defaults, `~/.config/akwb/config.yaml`,
  project `akwb.yaml` or `.akwb/config.yaml`, `AKWB_*` environment variables,
  and CLI overrides.
- `pydantic` validates types and log levels.

### Serialization

- `KnowledgeSerializer` abstraction with JSON, JSONL, and YAML implementations.
- `JsonlSerializer` rebuilds catalogs from `{kind, data}` records.

## Bug Fixes Since Pre-Release

- **Duplicate knowledge object IDs:** `AnalyzeEngine` no longer adds file objects
  unconditionally; Python files are only added when they contain children or
  imports.
- **Extraction result access:** `AnalyzeEngine` now uses `.value` to unwrap
  `ExtractionResult` objects.
- **Unknown evidence type:** `"extraction"` was added to the built-in evidence
  type registry.
- **Graph cycles:** `PythonSourceParser` no longer stores parent references on
  child knowledge objects, eliminating directed cycles in the graph.
- **CLI output formatting:** `akwb analyze` now prints the expected summary
  counts and exits `0` on success.

## Known Limitations

See `docs/KNOWN_ISSUES.md` for the full list. Highlights include:

- Plugin sandboxing and signature verification are not yet enforced.
- Secret scanning, audit logging, and resource watchdogs are not implemented.
- Graph and catalog serialization is not streaming; very large projects may
  consume significant memory.
- The CLI implements a subset of `docs/13_CLI_SPECIFICATION.md`.
- The repository root is missing a `README.md` and the version strings currently
  read `0.1.0`; these should be corrected before publishing the 1.0.0 artifact.

## Backward Compatibility

- This is the first public release; no migration is required.
- Workspace format is `workspace-v1`. Future major versions may introduce
  migration tooling.
- Python 3.12 or later is required.

## Upgrade Notes

If you installed a pre-release build from source, remove or back up any
existing `.akwb/` workspace and re-run `akwb analyze .` to regenerate artifacts
with the 1.0.0 format.

## Deprecations

None. This release has no prior public API to deprecate.

## Acknowledgments

This release was produced by the AKWB Team through the Sprint 7 integration and
wiring effort, turning the Sprint 3–6 framework components into a working
end-to-end knowledge compiler.
