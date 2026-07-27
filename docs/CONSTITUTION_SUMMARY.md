# AKWB Constitution Summary

**Version:** 1.0
**Status:** Ratified — Development Freeze, Sprint 6.5

This is a quick-reference summary of the AKWB Constitution. For the full text,
see `docs/AKWB_CONSTITUTION.md`.

---

## What AKWB Is

AKWB is an **Enterprise Knowledge Compiler** and **Engine**.

It transforms enterprise project information into canonical, reusable knowledge
artifacts and a `KnowledgeGraph`, stored in a project-owned `.akwb/` workspace.

It is **local-first**, **project-owned**, and **CLI-first**.

---

## The Mission

> Transform enterprise knowledge into canonical, reusable knowledge artifacts.

Nothing more.

---

## What AKWB Owns

- Discovery
- Parsing
- Normalization
- Extraction
- Knowledge Objects
- Knowledge Graph
- Workspace
- Export
- Plugin Framework
- Validation

---

## What AKWB Does Not Own

These belong to downstream products:

- AI Chat
- Agent Runtime
- Publishing
- CRM
- Business Dashboard
- Memory UI
- Workflow Automation
- Web UI
- Marketplace
- Prompt Builder
- Embeddings
- RAG
- Business Logic
- Cloud Operations

---

## Core Principles

- **Plugin-based** — every extensible surface is a port.
- **Local-first** — no network required.
- **Project-owned** — `.akwb/` belongs to the project.
- **Traceable** — every object and relationship has evidence.
- **Deterministic** — same inputs produce same outputs.
- **Reproducible** — workspaces can be regenerated.
- **No hidden mutations** — AKWB only writes to `.akwb/`.
- **Evidence before inference** — facts are grounded in source.
- **Small surface** — minimal CLI and API.
- **Stability over features** — contracts evolve slowly.

---

## The Workspace Contract

- `.akwb/` is the only public contract.
- Downstream products read artifacts, not engine internals.
- Artifacts are versioned and documented.
- Internal classes, modules, and functions are not a contract.

---

## Plugin Rules

- Plugins communicate only through public ports.
- Plugins are replaceable.
- Plugins do not modify engine internals.
- Plugins run with least privilege.
- Plugin API versions are explicit.
- Plugin execution is supervised.

---

## Compatibility

- Backwards compatible within a major version.
- Schema changes are additive or version-bumped.
- Migration is forward-only.
- Semantic versioning applies to engine, plugin API, and artifact schemas.

---

## Engineering Principles

- Explicit, typed, reviewed code.
- Contract-level testing.
- Deterministic outputs.
- Atomic writes.
- Incremental analysis.
- Observability without exposure of source content.

---

## Decision Framework

Every feature request must answer:

1. Does it belong inside AKWB?
2. Does it violate the product boundary?
3. Could it live in a downstream product?

If the answer to question 3 is yes, reject it.

---

## Success Definition

AKWB succeeds when a downstream product can consume a generated `.akwb/`
workspace without depending on AKWB internals.

---

## Amendment Rules

- The Constitution can only change through a formal Architecture Review.
- The roadmap cannot violate the Constitution.
- All contributors must uphold it.

---

## Related Documents

- `docs/AKWB_CONSTITUTION.md` — full constitution.
- `docs/ENGINE_PHILOSOPHY.md` — why these principles exist.
- `docs/ARCHITECTURAL_PRINCIPLES.md` — practical architectural guidance.
- `docs/DOWNSTREAM_CONTRACT.md` — contract with consuming products.
- `docs/PRODUCT_SCOPE.md` — product scope from the boundary review.
- `docs/PRODUCT_BOUNDARY_REVIEW.md` — approved product boundary review.
