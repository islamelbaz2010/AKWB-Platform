# AKWB Product Scope

## What AKWB Is

AKWB is a reusable **Enterprise Knowledge Extraction Engine**. Its single purpose
is to turn raw enterprise information—especially software project artifacts—into
canonical, machine-readable **Knowledge Objects** and a reusable **Knowledge
Graph**, then expose those artifacts through stable APIs and exports.

AKWB is an **engine**, not an application. It is designed to be consumed by
other products and tools.

### Core Responsibilities

1. **Discovery** — Scan project directories, classify files, fingerprint content,
   and build a `SourceCatalog`.
2. **Parsing & Normalization** — Read source files (Markdown, code, configs,
   documentation) and convert them into normalized structural representations.
3. **Extraction** — Derive typed `KnowledgeObject` candidates (decisions,
   components, requirements, business rules, etc.) from normalized content.
4. **Validation** — Ensure knowledge objects and relationships conform to a
   registered type system and carry evidence.
5. **Knowledge Graph Construction** — Build an in-memory graph of objects and
   relationships, index it, and support querying and traversal.
6. **Workspace Materialization** — Persist the `SourceCatalog`, `KnowledgeGraph`,
   and export artifacts into a project-owned `.akwb/` workspace.
7. **Export API** — Expose graph data and reports as JSONL, JSON, YAML, DOT, and
   Cypher files that downstream products can consume.
8. **Plugin Framework** — Allow third-party parsers, extractors, relationship
   builders, and graph backends to extend the engine without modifying core code.

### Consumption Model

AKWB is invoked as a CLI (`akwb analyze <path>`) and writes a self-contained
workspace under `.akwb/`. Downstream products read `.akwb/` artifacts or call
engine APIs to build their own UIs, agents, dashboards, and publishing flows.

Target downstream consumers include:

- **Eunoia AI OS** — consumes the knowledge graph and context artifacts for its
  own memory and agent runtime.
- **EPOS** — consumes exported Markdown/HTML reports and graph data for
  publishing.
- **AI Context Builder** — consumes JSONL/DOT/Cypher exports and context bundles
  to build model-specific prompts.
- **StayOS** — consumes the workspace index and reports for workspace productivity
  features.
- Future enterprise platforms that need a project knowledge foundation.

## What AKWB Is Not

AKWB is **not** an end-user platform. It deliberately avoids any capability that
is better owned by a downstream product with its own UI, workflow, or business
logic.

### Out of Scope

| Capability | Why It Is Outside AKWB |
|---|---|
| AI Chat UI | Conversational interfaces are product-specific. AKWB exposes context, not chat. |
| Workspace Dashboard UI | Visualization is a downstream concern; AKWB exports data, not rendered dashboards. |
| Publishing Platform | EPOS or another product should turn `.akwb/` exports into publishable sites. |
| Prompt Management UI | Prompt authoring, versioning, and testing belong to AI Context Builder. |
| Agent Runtime | Execution of agents, tools, or workflows is a downstream runtime concern. |
| Business Dashboards | Metrics, analytics, and executive reporting are product-specific. |
| Workflow Automation | Approval, review, and lifecycle workflows belong in consuming products. |
| Memory UI | User-facing memory search and conversation history belong in Eunoia AI OS. |
| CRM / HRMS Integration | Integrating with external business systems is a downstream adapter concern. |
| Source Code Editing | AKWB reads code; it never modifies project source. |
| Model Training / Fine-tuning | Training infrastructure is not an extraction concern. |
| Multi-tenant SaaS Operations | Hosting, billing, and tenant management are platform concerns, not the engine. |
| Plugin Marketplace UI | A marketplace is an ecosystem service; the engine only loads local plugins. |
| Real-time Collaboration / Chat | Multi-user editing and chat are product features, not engine responsibilities. |
| IDE-specific UI | IDEs can consume `.akwb/`; AKWB does not provide IDE panels or editors. |
| Authentication / SSO for End Users | Per-product identity decisions belong downstream. |

## Boundary Principle

AKWB stops at the **workspace artifact boundary**. It produces correct, versioned,
inspectable files under `.akwb/`. Everything that transforms those files into an
end-user experience, agent behavior, published site, or business workflow
belongs in a downstream product.

## Evidence from the Codebase

The following design decisions confirm the engine boundary:

- `docs/01_PRODUCT_VISION.md` states the goal is a CLI that creates a
  project-owned knowledge workspace modeled after `.git`.
- `docs/EXTRACTION_PIPELINE.md` explicitly says the pipeline contains no
  AI-specific business logic, report generation, or publishing logic.
- `src/akwb/cli.py` currently exposes `version`, `init`, `doctor`, and
  `discover`—purely engine operations. There is no `chat`, `dashboard`, or
  `publish` command.
- `src/akwb/extraction/pipeline.py` produces `ExtractionResult` objects, not
  UI-rendered reports.
- `src/akwb/graph/engine.py` exports graph data through programmatic APIs, not
  a web interface.

## Conclusion

AKWB is correctly scoped as a knowledge extraction and graph engine. The risk
is not scope ambiguity; the risk is scope creep into consumer-facing features
such as AI summarization, chat, dashboards, and publishing. The roadmap must
preserve this boundary.
