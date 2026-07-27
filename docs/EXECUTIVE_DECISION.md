# AKWB Sprint 7 Executive Decision

**Date:** 2026-07-27  
**Decision:** GO — proceed with Sprint 7 as an integration sprint.  
**Approver:** Project Director (pending signature)

---

## Decision

**Approve Sprint 7.** The remaining work to make AKWB a usable Enterprise
Knowledge Compiler is implementation and integration, not architecture.

No changes to the AKWB Constitution, product boundary, or architecture are
required.

## Why GO

| Criterion | Assessment |
|---|---|
| **Architecture is sound** | Clean Architecture, plugin ports, local-first design, and `.akwb/` contract are all in place and tested. |
| **Components exist and pass tests** | Discovery, Knowledge Framework, Extraction Pipeline, Graph Engine, and Markdown Parser are implemented and all tests pass (`python3 -m pytest -q` = 100%). |
| **No architecture changes needed** | The blockers are wiring, persistence, CLI commands, and a basic code parser. No new engines or abstractions are required. |
| **MVP scope is controlled** | The Constitution forbids AI, UI, marketplace, and cloud work. The audit confirms none of these are needed for MVP. |
| **Risk is bounded** | The shortest path to MVP is known and documented in `docs/SPRINT_7_EXECUTION_PLAN.md`. Each task is independently reviewable. |

## Primary Blockers to Close

1. `akwb analyze` command is missing.
2. `Container` does not wire `ExtractionPipeline` or `GraphEngine`.
3. No graph persistence backend (`LocalGraphStorage`).
4. No `KnowledgeCatalog` assembly from extraction results.
5. No relationship extraction.
6. No `report` / `export` commands.
7. CLI does not load plugins.
8. No Python source-code parser.

All blockers are listed with severity and required fixes in
`docs/MVP_BLOCKERS.md`.

## What Sprint 7 Must Produce

1. A working `akwb analyze <path>` command.
2. A persisted `.akwb/` workspace containing:
   - `index/source_catalog.jsonl`
   - `knowledge/graph_nodes.jsonl`
   - `knowledge/graph_edges.jsonl`
   - `graph/graph.jsonl`, `graph/graph.dot`, `graph/graph.cypher`
   - `reports/summary.md`, `reports/summary.json`
3. `akwb report` and `akwb export` commands.
4. Basic Python source-code extraction.
5. End-to-end integration tests.
6. Passing MVP acceptance test defined in `docs/MVP_ACCEPTANCE_TEST.md`.

## What Sprint 7 Must NOT Produce

- AI summarization, embeddings, RAG, or chat features.
- Plugin marketplace.
- Web dashboard, IDE UI, or business analytics.
- Cloud hosting, multi-tenancy, or SaaS operations.
- Node.js, Java, Go, Rust, PHP parsers.
- New engines, new abstractions, or architecture changes.

## Investment Committee Rationale

### Minimize

- **Time:** Sprint 7 is a focused integration sprint. No research or architecture.
- **Complexity:** Existing components are reused. Only glue, persistence, and a
  minimal Python parser are added.
- **Cost:** No external services, models, or infrastructure.
- **Risk:** Scope is tightly bounded by the Constitution and acceptance test.

### Maximize

- **Business Value:** `akwb analyze` makes the product usable and enables
  downstream products.
- **Reusability:** `.akwb/` becomes a stable contract for Eunoia, EPOS, AI
  Context Builder, and StayOS.
- **Stability:** All work is additive and tested. No breaking architecture
  changes.

## Conditions for Aborting Sprint 7

Escalate to Architecture Review and consider NO-GO if any of the following
occur:

1. A task requires a new engine, abstraction, or Constitutional change.
2. The plugin API or workspace schema must be redesigned.
3. The MVP acceptance test in `docs/MVP_ACCEPTANCE_TEST.md` cannot be met
   without expanding scope beyond the blockers listed above.

## Next Step

Begin Sprint 7 implementation in order of the task breakdown in
`docs/SPRINT_7_EXECUTION_PLAN.md`. Stop if any condition for aborting is met.

## Supporting Documents

- `docs/MVP_READINESS_AUDIT.md` — full audit with all 10 sections.
- `docs/VERTICAL_SLICE_ANALYSIS.md` — why `akwb analyze` fails today.
- `docs/MVP_BLOCKERS.md` — ranked list of MVP blockers.
- `docs/SPRINT_7_EXECUTION_PLAN.md` — task breakdown for Sprint 7.
- `docs/MVP_ACCEPTANCE_TEST.md` — official MVP acceptance test.

---

**Decision:** GO  
**Sprint 7 is approved to begin.**
