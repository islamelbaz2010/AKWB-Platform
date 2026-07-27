# Sprint 1 Execution Plan

## 1. Purpose

This plan defines the work for **Sprint 1: Foundation**. The goal is to implement the repository skeleton, core services, and the first end-to-end analysis path in conformance with `ARCHITECTURE_FREEZE_v1.md` and `IMPLEMENTATION_GUIDE.md`.

## 2. Sprint Goal

Deliver a working CLI that can:

- Run `akwb init` to create a `.akwb/` workspace.
- Run `akwb doctor` to validate the environment.
- Run `akwb analyze` on a fixture project to produce a `SourceCatalog` with fingerprints.
- Load a stub plugin through the plugin registry.
- Pass lint, type-check, and unit tests on Ubuntu, macOS, and Windows.

## 3. Sprint Boundaries

- **Start:** Implementation approval of `ARCHITECTURE_FREEZE_v1.md`.
- **Duration:** 2 weeks.
- **End:** Foundation Demo + Sprint Retrospective.
- **Out of scope:** Real parser/extractor plugins, full graph build, AI context, reports, marketplace, remote install.

## 4. Task Breakdown

| # | Task | Owner | Dependencies | Acceptance Criteria | Est. Days |
|---|---|---|---|---|---|
| 1 | Create repository skeleton and `pyproject.toml` | Principal Engineer | None | `src/akwb/` package exists; `python -m akwb` prints version; no import cycles. | 1 |
| 2 | Implement `akwb.types` shared kernel | Principal Engineer | Task 1 | `Result`, `Diagnostic`, identifier primitives, serialization helpers present and unit-tested. | 1 |
| 3 | Implement `akwb.domain` core entities and events | Principal Engineer | Task 2 | `Project`, `SourceEntry`, `KnowledgeUnit`, `Relationship`, `Artifact`, `Snapshot`, `ArtifactManifest`, domain events, repository interfaces. | 2 |
| 4 | Implement `akwb.events` typed event bus | Principal Engineer | Task 1 | In-memory publish/subscribe; `EventEnvelope` with id, timestamp, correlation; unit tests. | 1 |
| 5 | Implement `akwb.observability` (logger, metrics, progress) | DevOps / Platform | Task 1 | Structured logs, progress events, diagnostic collector; unit tests. | 1 |
| 6 | Implement `akwb.config` loader/merger/validator | Config Lead | Task 1 | Loads defaults/global/project/env/CLI; validates with Pydantic; stores effective snapshot. | 2 |
| 7 | Implement `akwb.unit_of_work` and `akwb.storage` ports | Storage Lead | Task 3, 4 | `StoragePort`, `ProjectRepository`, `SourceCatalogRepository`, `MemoryStorageBackend`, `LocalStorageBackend` with atomic writes. | 2 |
| 8 | Implement `akwb.plugins` loader, registry, and sandbox basics | Plugin Lead | Task 6, 7 | Discovers plugins from path, validates `plugin.yaml`, loads Python plugin module, enforces `filesystem` permission. | 2 |
| 9 | Implement `akwb.kernel` DI container and scheduler | Principal Engineer | Tasks 2-8 | Wires components; schedules Discovery Engine; handles lifecycle. | 2 |
| 10 | Implement `akwb.engines.discovery` file walker and fingerprinter | Discovery Lead | Tasks 3, 4, 7 | Produces `SourceCatalog` with fingerprints for fixture; respects ignore patterns and size limits. | 2 |
| 11 | Implement `akwb.engines.incremental` diff and change set | Incremental Lead | Tasks 3, 7, 10 | Compares prior/current catalogs; emits change set and invalidation list. | 1 |
| 12 | Implement `akwb.cli` commands `init`, `doctor`, `version`, `analyze` | CLI Lead | Tasks 6, 9, 10, 11 | Commands dispatch; `init` creates workspace; `doctor` validates env; `analyze` runs discovery and writes catalog. | 2 |
| 13 | Implement `akwb.security` secret scanner stub and audit logger | Security Lead | Tasks 1, 5 | Scans for known secret patterns; redaction stub; audit log writes to `.akwb/logs/audit.log`. | 2 |
| 14 | Create canonical fixtures and contract harness | Test Lead | Task 10 | `fixtures/python`, `fixtures/nodejs`, `fixtures/mixed`, `fixtures/docs-only` with expected outputs; contract harness can load a stub detector. | 2 |
| 15 | Set up CI pipeline (lint, type check, unit tests) | DevOps Lead | Task 1 | GitHub Actions / equivalent runs `ruff`, `mypy`, `pytest` on Ubuntu, macOS, Windows for every PR. | 2 |
| 16 | Write ADRs for runtime, storage, plugin API, AI, telemetry | Principal Engineer | All tasks | ADRs in `docs/ADRs/` reflecting freeze decisions. | 1 |

## 5. Sprint Schedule (2 Weeks)

### Week 1: Skeleton and Core Services

- **Day 1-2:** Tasks 1, 2, 3, 16 (repository, types, domain, ADR drafting).
- **Day 3-4:** Tasks 4, 5, 6 (event bus, observability, config).
- **Day 5:** Tasks 7, 8 (storage and plugin registry).
- **Daily:** Sync 15 min, blockers escalated immediately.

### Week 2: Engines, CLI, and Integration

- **Day 6-7:** Tasks 9, 10 (kernel, discovery engine).
- **Day 8:** Tasks 11, 13 (incremental, security).
- **Day 9-10:** Tasks 12, 14 (CLI, fixtures, contract harness).
- **Day 10:** Task 15 (CI finalization) and buffer.
- **Day 11-13:** Buffer, integration, bug fixing, documentation.
- **Day 14:** Demo and retrospective.

## 6. Critical Path

The critical path is:

`Task 1 → Task 2 → Task 3 → Task 7 → Task 8 → Task 9 → Task 10 → Task 11 → Task 12`

Any delay on this path threatens the sprint goal. Tasks 4, 5, 6, 13, 14, 15 can run in parallel.

## 7. Definition of Done

- [ ] All tasks merged to `main`.
- [ ] CI passes on all three platforms.
- [ ] `akwb init`, `akwb doctor`, and `akwb analyze` run on `fixtures/mixed` and produce a valid `SourceCatalog`.
- [ ] `mypy --strict` and `ruff` report zero issues.
- [ ] Domain, events, storage, and plugin modules have >80% unit test coverage.
- [ ] No cyclic dependencies.
- [ ] ADRs are approved and committed.

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Plugin sandbox proves harder than expected in Python | High | Start with path validation; defer OS sandbox to Sprint 2. |
| CI flakiness on Windows paths | Medium | Use `pathlib` and test on Windows early (Day 4). |
| Configuration merging edge cases | Medium | Pydantic validation; unit tests for all precedence combinations. |
| Team unfamiliar with Clean Architecture dependency rule | Medium | Daily architecture review of new imports; CI import-lint gate. |

## 9. Sprint Review Agenda

1. Demo: `akwb init`, `akwb doctor`, `akwb analyze` on a fixture project.
2. Architecture conformance review: no cyclic deps, no core plugin imports.
3. CI and test report.
4. Readiness check for Sprint 2 (knowledge engine).
