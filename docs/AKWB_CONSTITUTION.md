# AKWB Constitution

**Version:** 1.0
**Status:** Ratified — Development Freeze, Sprint 6.5

> This document is the supreme authority of the AKWB project. It defines the
> immutable principles that govern code, architecture, roadmap, and
> contribution. No feature, pull request, or roadmap change may violate this
> constitution. Amendments require a formal Architecture Review.

---

## Preamble

AKWB exists because enterprise knowledge is fragmented, opaque, and trapped
inside source files, documents, configuration, and tribal memory.

Software projects, in particular, accumulate decisions, dependencies,
requirements, and context across thousands of files. These artifacts contain
valuable knowledge, but they are not structured, not queryable, and not
reusable. Every downstream product—every AI assistant, dashboard, search
engine, and publishing platform—must rediscover the same facts.

AKWB was created to solve this problem once, at the source. It is a single,
reusable **Enterprise Knowledge Compiler** that transforms raw enterprise
information into canonical, typed, traceable, and portable knowledge
artifacts. It performs this transformation offline, locally, and under the
project's own control.

AKWB intentionally has limited scope. It does not pretend to be the final
product. It does not serve end users, run agents, publish documents, manage
workflows, or make business decisions. It exists so that other products can do
those things better—because they consume a clean, stable, trustworthy knowledge
foundation instead of parsing raw files themselves.

The constitution is short because the project is narrow. The permanence of
these rules is more important than the speed of adding features.

---

## Article I — Identity

AKWB is defined permanently as:

### 1.1 Enterprise Knowledge Compiler

AKWB compiles enterprise information—source code, documentation, configuration,
schemas, and related artifacts—into a structured knowledge representation. It
is a compiler, not a runtime.

### 1.2 Engine

AKWB is an engine. It has no end-user interface, no chat, no dashboard, no
workflow engine, and no business logic. It runs inside CI pipelines, developer
workstations, and downstream services. The products people interact with are
built downstream.

### 1.3 Local First

AKWB runs where the project lives. It does not require cloud connectivity,
remote APIs, or network access to perform its core function. External calls are
explicit, optional, and off by default.

### 1.4 Project Owned

All generated artifacts belong to the project. They reside in the `.akwb/`
directory, travel with the repository, and are readable by the project owners.
No vendor, service, or third party owns the workspace.

### 1.5 CLI First

The primary interface is a command-line tool. The command surface is small and
stable. Downstream products consume artifacts, not a live service.

---

## Article II — Mission

The mission of AKWB is singular and permanent:

> Transform enterprise knowledge into canonical, reusable knowledge artifacts.

Nothing more.

AKWB does not interpret, decide, publish, automate, or present. It extracts,
validates, structures, and exposes. Every downstream product is free to build
its own interpretation and presentation on top of the generated artifacts.

The mission succeeds when any downstream product can understand a project by
reading its `.akwb/` workspace.

---

## Article III — Product Boundary

AKWB owns only the following responsibilities. Anything not on this list does
not belong in AKWB.

1. **Discovery** — locating, classifying, fingerprinting, and inventorying
   project sources.
2. **Parsing** — reading source files and producing normalized structural
   representations.
3. **Normalization** — converting heterogeneous inputs into a common content
   model.
4. **Extraction** — deriving typed knowledge objects and relationships from
   normalized content.
5. **Knowledge Objects** — the canonical data model, type system, evidence,
   validation, and traceability.
6. **Knowledge Graph** — building, indexing, querying, traversing, validating,
   and persisting the graph of knowledge objects and relationships.
7. **Workspace** — materializing artifacts into the project-owned `.akwb/`
   directory in a stable, versioned format.
8. **Export** — producing standard, machine-readable exports (JSONL, JSON,
   YAML, DOT, Cypher, Markdown) from the knowledge graph and workspace.
9. **Plugin Framework** — defining public ports and loading plugins that extend
   the engine without modifying it.
10. **Validation** — ensuring artifacts, objects, relationships, and graphs
    conform to their declared contracts.

AKWB stops at the boundary of `.akwb/`. It does not cross into user
experiences, business workflows, AI runtimes, or cloud operations.

---

## Article IV — Forbidden Responsibilities

The following capabilities are explicitly forbidden inside AKWB. They belong to
downstream products and must never become engine features.

- **AI Chat** — conversational interfaces belong in AI products.
- **Agent Runtime** — executing agents, tools, or workflows belongs in
  downstream runtimes.
- **Publishing** — turning artifacts into published sites, documents, or
  branded reports belongs in publishing products.
- **CRM** — customer, sales, or business relationship management belongs in
  business systems.
- **Business Dashboard** — analytics, metrics, and executive reporting belong in
  analytics products.
- **Memory UI** — user-facing memory search, history, and recall belong in AI
  operating systems.
- **Workflow Automation** — approval, review, and lifecycle workflows belong in
  collaboration and BPM products.
- **Web UI** — web interfaces, visual exploration, and dashboards belong in
  downstream applications.
- **Marketplace** — plugin distribution, signing, discovery, and commerce belong
  in an ecosystem marketplace, not the engine loader.
- **Prompt Builder** — prompt authoring, versioning, and testing belong in AI
  context products.
- **Embeddings** — vector generation and semantic search indexes belong in AI
  products.
- **RAG** — retrieval-augmented generation orchestration belongs in AI products.
- **Business Logic** — rules, policies, approvals, and decisions belong in
  downstream business systems.
- **Cloud Operations** — multi-tenant hosting, billing, scaling, and tenant
  management belong in platform and SaaS products.

If a feature request matches any item in this list, it must be rejected or
redirected to the appropriate downstream product.

---

## Article V — Architectural Principles

Every design decision in AKWB must respect these principles:

### 5.1 Plugin-Based

Every extensible surface is exposed through a public port. Built-in
implementations are themselves plugins. No component is hard-coded beyond the
contracts required to load plugins.

### 5.2 Local First

The engine runs without network access. External models, services, and APIs are
explicitly opt-in. Workspace artifacts are local files.

### 5.3 Project Owned

The `.akwb/` directory belongs to the project. It is versionable, inspectable,
deletable, and portable. The engine writes it; the project owns it.

### 5.4 Traceable

Every knowledge object and relationship must carry evidence: a source path, a
span, a confidence, and a provenance chain. Nothing is accepted on faith.

### 5.5 Deterministic

Given the same inputs and the same configuration, AKWB produces the same
outputs. Non-determinism is a bug unless explicitly declared and justified.

### 5.6 Reproducible

A downstream product must be able to reproduce the workspace from a known
project state and a known AKWB version.

### 5.7 No Hidden Mutations

AKWB never silently modifies source code, project files, or git history. It
only writes to `.akwb/`.

### 5.8 Evidence Before Inference

Relationships and facts must be grounded in source evidence. Probabilistic or
inferred claims must be labeled with confidence and justification.

### 5.9 Small Surface

The CLI, the public API, and the plugin surface must remain small. Complexity
is delegated to plugins and downstream products.

### 5.10 Stability Over Features

A stable, narrow engine is more valuable than a broad, unstable one. Contracts
and schemas evolve carefully; features that threaten contract stability are
rejected.

---

## Article VI — Workspace Contract

### 6.1 The Contract

The `.akwb/` directory is the only public contract between AKWB and downstream
products. No downstream product may depend on internal classes, functions,
modules, or implementation details of the engine.

### 6.2 Artifact-First Consumption

Downstream products consume artifacts. Artifacts are files inside `.akwb/` with
stable schemas and documented formats.

### 6.3 Schema Versioning

Every artifact schema is versioned independently. Breaking changes require a
new schema version and a documented migration path.

### 6.4 Inspectability

All artifacts are human-readable where practical. JSON, JSONL, YAML, Markdown,
DOT, and Cypher are preferred over opaque binary formats.

### 6.5 No Backdoors

AKWB must not write hidden state, hidden caches, or hidden configuration
outside `.akwb/`. The workspace is self-contained.

---

## Article VII — Plugin Constitution

### 7.1 Public Contracts Only

Plugins communicate with AKWB only through published ports and public data
contracts. They may not access engine internals.

### 7.2 Replaceability

Any built-in implementation may be replaced by a plugin without changing the
rest of the engine. The engine must not favor its own implementations.

### 7.3 No Internal Mutation

Plugins must not modify the engine, the workspace, or source files outside the
contracts provided by their port.

### 7.4 Least Privilege

Plugins declare the permissions they need. The engine enforces those
permissions. A parser that reads files must not gain network access.

### 7.5 Versioned Contracts

Plugin API versions are explicit. The engine may support multiple contract
versions during a deprecation window, but never silently.

### 7.6 Sandboxed Execution

Plugin code runs under the engine's supervision. Unsafe operations, path
escapes, and undeclared side effects are rejected.

---

## Article VIII — Compatibility

### 8.1 Backwards Compatibility

The `.akwb/` workspace format and the plugin API must remain backwards
compatible within a major version. A workspace produced by an older AKWB
version must remain readable by newer versions.

### 8.2 Schema Evolution

Schema changes follow these rules:

- Additive changes are allowed.
- Breaking changes require a new schema version.
- Removed fields are deprecated before removal.
- Migration code is provided when the engine cannot read the old format natively.

### 8.3 Versioning

AKWB follows semantic versioning for the engine, the plugin API, and each
artifact schema.

### 8.4 Migration Philosophy

AKWB migrates data forward, not backward. Downstream products are expected to
consume the current documented schema. Legacy support is limited to one major
version behind.

---

## Article IX — Engineering Principles

### 9.1 Code Quality

Code is explicit, typed, and reviewed. Cleverness is avoided. Readability and
maintainability are more important than brevity.

### 9.2 Testing

Every public contract is tested. Deterministic behavior is tested with fixed
fixtures. Plugin ports are tested with reference implementations.

### 9.3 Typing

Static types document contracts. Public APIs use explicit type signatures.
Runtime behavior must not contradict declared types.

### 9.4 Documentation

Every public port, artifact, and CLI command is documented. Documentation is
as permanent as code. Undocumented behavior does not exist.

### 9.5 Deterministic Outputs

The same inputs, in the same environment, must produce byte-for-byte identical
artifacts where feasible. Non-determinism is isolated, measured, and declared.

### 9.6 Atomic Writes

Workspace writes are atomic. A reader must never observe a partially written
artifact. Temporary writes are completed before being promoted to final paths.

### 9.7 Observability

The engine records diagnostics, progress, and metrics. It does not leak
sensitive source content into logs. Observability is for troubleshooting, not
for surveillance.

### 9.8 Least Surprise

Default behavior is incremental, local, and safe. Destructive or irreversible
actions require explicit flags.

---

## Article X — Decision Framework

Every future feature request, pull request, and roadmap change must answer the
following questions:

1. **Does it belong inside AKWB?**
   It must fit within Article III.

2. **Does it violate the product boundary?**
   It must not match Article IV.

3. **Could it live in a downstream product?**
   If the feature is primarily a user experience, AI behavior, business rule,
   workflow, or presentation, it belongs downstream.

If the answer to question 3 is yes, the request is rejected. AKWB does not
absorb downstream responsibilities to make the engine larger.

---

## Article XI — Success Definition

AKWB succeeds when a downstream product can consume a generated `.akwb/`
workspace without needing to import, link, or depend on AKWB internals.

Success is not measured by the number of features in the engine. Success is
measured by the number and quality of downstream products enabled by the
engine.

---

## Article XII — Amendment Rules

### 12.1 Supremacy

This Constitution takes precedence over any roadmap, sprint plan, or technical
decision. No feature may violate it.

### 12.2 Amendment Process

The Constitution may only be amended through a formal Architecture Review. The
review must:

- Identify the principle to be changed.
- Justify why the change is necessary.
- Describe the impact on existing contracts, artifacts, and downstream
  products.
- Receive explicit approval from the project leadership.

### 12.3 Roadmap Subordination

The roadmap must comply with the Constitution. A roadmap change that conflicts
with this document is invalid until the Constitution is amended.

### 12.4 Contributor Obligation

Every contributor, maintainer, and reviewer is responsible for knowing and
upholding this Constitution. Ignorance of these rules is not an excuse for
violating them.

---

## Signature

This Constitution is the permanent foundation of the AKWB project. It is
binding on all future work.
