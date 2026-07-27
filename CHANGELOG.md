# Changelog

All notable changes to the AKWB Platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-27

### Added

- Initial public release of the AKWB Knowledge Workspace platform.
- Local-first analysis pipeline: discover, extract, validate, graph, and report.
- CLI commands: `init`, `analyze`, `discover`, `doctor`, `report`, `export`, `version`.
- Project-owned `.akwb/` workspace with `workspace.json`, `knowledge/catalog.jsonl`,
  `graph/graph.{jsonl,dot,cypher}`, `reports/summary.{md,json}`, and `logs/analysis.log`.
- Knowledge object framework with typed objects, relationships, evidence, and validators.
- In-memory knowledge graph engine with DOT and Cypher exports.
- Markdown and Python source extraction.
- Plugin loader and registry using a port-based extension model.
- Configuration layering: defaults, `akwb.yaml`, `.akwb/config.yaml`, environment
  variables (`AKWB_*`), and CLI overrides.
- Comprehensive documentation in `docs/` covering architecture, CLI, security,
  performance, testing, and known limitations.

### Changed

- Release metadata updated to version `1.0.0` in `pyproject.toml` and
  `src/akwb/_version.py`.
- `Development Status` classifier moved from `3 - Alpha` to `5 - Production/Stable`.
- Expanded project keywords and URLs in `pyproject.toml`.

### Fixed

- Version strings aligned across workspace metadata, tests, and fixtures.
- Documentation aligned to mark post-MVP or planned features explicitly.
- Real static-analysis issues reported by `mypy` and `ruff` addressed.

### Known Limitations

- Plugin sandboxing, signature verification, secret scanning, audit logging, and
  resource limits are not implemented in 1.0.0; they are documented as
  post-MVP/planned in the security model.
- Concurrency, streaming, content-addressable caches, and SQLite graph spill are
  not implemented; the performance strategy marks these as post-MVP/planned.
- CLI commands such as `update`, `status`, `config`, `plugin`, `clean`, `ask`, and
  `ci` are not yet implemented; see `docs/13_CLI_SPECIFICATION.md`.
- The implementation uses a flatter module layout than the long-term architecture
  described in `docs/IMPLEMENTATION_GUIDE.md`.
