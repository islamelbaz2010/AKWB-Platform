# AKWB Roadmap

This roadmap reflects the state of the project at the 1.0.0 MVP release and
outlines the planned path toward a full Enterprise Knowledge Compiler.

## 1.0.0 MVP (current)

- [x] End-to-end local analysis pipeline.
- [x] CLI commands: `init`, `analyze`, `discover`, `doctor`, `report`, `export`, `version`.
- [x] Knowledge object framework and validators.
- [x] In-memory knowledge graph with JSONL, DOT, and Cypher exports.
- [x] Workspace materialisation under `.akwb/`.
- [x] Plugin loader and registry.
- [x] Markdown and Python source extraction.
- [x] Configuration layering and validation.
- [x] Static analysis target (`mypy`) met.

## 1.0.1 — 1.1.0 (short term)

- [ ] `akwb status` and `akwb update` for incremental workspace refresh.
- [ ] `akwb config` to read and write effective configuration.
- [ ] `akwb plugin list` and `akwb clean`.
- [ ] Root quick-start and `CONTRIBUTING.md` polish (already introduced in 1.0.0 RC1).
- [ ] `akwb report coverage` and `--format` support.

## 1.2.0 (medium term)

- [ ] Plugin sandboxing, permission enforcement, and signature verification.
- [ ] Secret scanning and redaction before writing artifacts.
- [ ] Audit logging for plugin loads, configuration changes, and security events.
- [ ] Resource watchdog (CPU, memory, file-size limits).
- [ ] Benchmark suite for the performance targets in `docs/17_PERFORMANCE_STRATEGY.md`.

## 2.0.0 (long term)

- [ ] Streaming, multi-threaded, and process-pool execution for discovery and extraction.
- [ ] Content-addressable parse/extract cache and incremental invalidation graph.
- [ ] SQLite-backed graph storage and query indexes.
- [ ] Memory engine and AI context bundles.
- [ ] Embeddings and vector search (local-first, opt-in).
- [ ] Plugin marketplace and signed workspace artifacts.
- [ ] Multi-graph support and workspace migration tooling.

## How to Influence the Roadmap

Open an issue describing the use case or enhancement. Post-MVP features are
labelled `post-mvp` and welcome community discussion.
