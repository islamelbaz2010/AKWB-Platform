# Ready for Implementation

> **Superseded by `READY_FOR_SPRINT_1.md` and `ARCHITECTURE_FREEZE_v1.md`.** This document captured the pre-freeze assessment. The Architecture Freeze v1 closes all open decisions and authorizes Foundation Sprint 1 to begin.

## Status

**NOT READY for feature implementation (as of pre-freeze).**

Sprint 0 produced a strong architectural foundation, but production feature code (parsers, extractors, AI context, marketplace) **must not be written** until five critical architectural decisions are closed and documented.

## Why Implementation Should Not Begin

1. **Implementation language/runtime is not selected.**
   - Module layout, packaging, concurrency, and GIL strategy depend on this choice.
2. **Plugin runtime isolation and port contract are not formalized.**
   - Without concrete request/response schemas and lifecycle hooks, plugins cannot be built or contract-tested.
3. **Storage backend and indexing strategy were not decided at the time of this assessment.**
   - The workspace, cache, and query performance depend on this choice.
4. **AI/embedding model strategy is unresolved.**
   - Local vs. remote models, licensing, size, and privacy impact must be decided before AI engine work.
5. **Telemetry, error-reporting, and update-check policy is not documented.**
   - Any network code or crash reporting without a policy violates the privacy/security non-functional requirements.

Additional risks that block feature work:
- No formal threat model for plugin execution or the marketplace.
- No canonical fixture projects or contract-test golden outputs.
- No workspace schema migration strategy beyond high-level versioning.
- Cross-language relationship resolution heuristics are undefined.

## What Is Approved: Foundation Sprint 1

A **Foundation Sprint 1** is approved. Its goal is to close the critical decisions above and build the implementation skeleton. This is architectural closure and infrastructure scaffolding, not feature implementation.

## Sprint 1 Backlog

| # | Story | Acceptance Criteria | Owner |
|---|---|---|---|
| 1 | Select implementation language/runtime | Decision record in `docs/adr/001-runtime.md`; team sign-off; runtime prototype passes a file-walk and fingerprint benchmark. | Principal Engineer |
| 2 | Define plugin port request/response schemas | `docs/PLUGIN_API_SPEC.md` with typed schemas, lifecycle hooks, and error contracts; example stub plugin implemented. | Plugin Lead |
| 3 | Decide storage backend and indexing strategy | ADR in `docs/adr/002-storage.md`; prototype reads/writes `SourceCatalog` and `KnowledgeGraph` within performance budget. | Storage / Performance Lead |
| 4 | Decide AI/embedding/summarization model strategy | ADR in `docs/adr/003-ai.md`; default is local-first and optional; external model opt-in path documented. | AI Lead |
| 5 | Document telemetry, error-reporting, and update-check policy | `docs/TELEMETRY_POLICY.md` approved; config flags for `enableTelemetry` and `enableUpdateCheck` default to `false`. | Security / Product Owner |
| 6 | Produce formal threat model | `docs/THREAT_MODEL.md` covering plugin execution, sandbox escape, remote install, and data exfiltration. | Security Architect |
| 7 | Create repository skeleton and DI container | `akwb` package with `cli`, `kernel`, `config`, `domain`, `events`, `observability`, `unit_of_work`, `storage`, `plugins`, `incremental` modules; dependency graph has no cycles. | Principal Engineer |
| 8 | Implement configuration loader and merger | Loads defaults, global, project, CLI flags, and `AKWB_*` environment variables; validates schema; writes snapshot. | Config Lead |
| 9 | Implement `akwb init` and `akwb doctor` | `init` creates `.akwb/`, default config, and `.gitignore` guidance; `doctor` validates environment, plugins, and permissions. | CLI Lead |
| 10 | Implement file walker and fingerprint utility | Discovery Engine produces a `SourceCatalog` with fingerprints for `fixtures/mixed`; respects ignores and size limits. | Discovery Lead |
| 11 | Define canonical fixtures and contract-test harness | `fixtures/python`, `fixtures/nodejs`, `fixtures/mixed`, `fixtures/docs-only` with expected `SourceCatalog` and report snapshots; harness validates a stub detector. | Test Lead |
| 12 | Set up CI pipeline | Lint, type check, unit tests, and security scans run on Ubuntu, macOS, and Windows for every PR. | DevOps Lead |
| 13 | Draft workspace schema migration contract | Document how `schemaVersion` in `workspace.json` triggers migration hooks and how backward compatibility is maintained. | Data Model Lead |
| 14 | Spike cross-language relationship resolution | Report on how Python/JavaScript, Python/C, and package imports are resolved and what alias tables detectors must provide. | Knowledge Engine Lead |

## Readiness Gate for Sprint 2

Sprint 2 feature work can only begin after all of the following are true:

- [ ] Implementation runtime ADR approved.
- [ ] Plugin port API spec approved and at least one stub plugin passes contract tests.
- [ ] Storage backend ADR approved and prototype benchmark meets the 1M LOC / 5 min cold-analysis budget or has a mitigation plan.
- [ ] AI/embedding ADR approved.
- [ ] Telemetry policy approved and config flags implemented.
- [ ] Threat model reviewed and accepted.
- [ ] `akwb init`, `akwb doctor`, and file walker end-to-end test passes.
- [ ] CI pipeline passes on all three platforms.
- [ ] Canonical fixtures and contract-test harness are in place.

## Conclusion

AKWB is **ready for Foundation Sprint 1** and **not ready for feature implementation**. Closing the five critical architectural decisions in Sprint 1 will make the platform implementable and de-risk later sprints.
