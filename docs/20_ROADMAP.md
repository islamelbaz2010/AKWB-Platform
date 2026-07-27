# Roadmap

## Purpose
Sequence the work from architecture approval through production-ready releases and future evolution.

## Responsibilities
- Define phases and sprint themes.
- Prioritize features and architectural enablers.
- Identify dependencies between deliverables.
- Set release milestones.

## Phase 1: Foundation (Sprints 1–3)
- Core CLI entry point, config loading, DI container, and event bus.
- Domain model and storage abstraction.
- Local workspace layout and manifest.
- Discovery Engine with basic file classification and fingerprinting.
- Plugin loader and sandbox (minimum viable).

## Phase 2: Knowledge Extraction (Sprints 4–6)
- Parser/extractor plugin API and reference implementations for Python and Node.js.
- Knowledge graph construction and basic relationship inference.
- Incremental analysis end-to-end.
- Cache and fingerprinting fully wired.

## Phase 3: AI Context & Reports (Sprints 7–9)
- AI Engine context builders and summarization.
- Chunking and optional local embeddings.
- Report generation: structure, coverage, graph.
- Graph exports in JSONL, DOT, and Cypher.

## Phase 4: Ecosystem & Hardening (Sprints 10–12)
- Plugin marketplace and signatures.
- Security hardening and secret scanning.
- Cross-platform packaging and CI.
- Performance benchmarking and optimization.
- Public beta release.

## Phase 5: Scale & Enterprise (Future)
- Remote and distributed analysis.
- Team workspace federation.
- Web dashboard and API.
- Enterprise policy and SSO.
- Advanced traceability linking requirements, tests, and runtime traces.

## Inputs
- Product vision and requirements.
- Architecture documents.
- Team capacity and business priorities.

## Outputs
- Release plan.
- Sprint backlogs.
- Milestone acceptance criteria.

## Dependencies
- All preceding architecture documents.

## Future Extensions
- IDE extensions and editor plugins.
- CI/CD integrations and watch-mode daemon.
- Multi-project knowledge graphs.
- Federated enterprise workspaces.

## Risks
- Scope expansion delays the core release.
- Plugin ecosystem adoption is uncertain.
- Competing tools reduce differentiation.

## Design Decisions

- Sprint 0 (this architecture) must be approved before any feature code is written.
- Phase 1 closes the implementation language/runtime, plugin API signature, storage backend, and telemetry policy decisions.
- Each phase ends with a readiness gate: design review, contract tests, performance benchmark, and security review.
- Marketplace and remote registry work is gated on CLI/plugin API stability and a signed plugin distribution workflow.
- Enterprise features (federation, SSO, dashboard) are deferred until the public beta is stable.
- Release early with Python and Node.js support, then expand to other languages.
- CLI and plugin API are stabilized before the marketplace launch.
- Incremental analysis is built in from Phase 1 to avoid retrofitting later.
