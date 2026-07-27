# Publishing Architecture

## Purpose

Define the architecture that transforms a discovered and analyzed project into a **project-specific, governed, enterprise knowledge publication**. This architecture is output-format and project-type agnostic: it decides *what* knowledge assets to publish and *why*, then delegates *how* and *where* to plugin-driven generators and exporters.

## Responsibilities

- Provide a bounded context for **knowledge publishing** on top of Discovery, Knowledge, Graph, Memory, and AI engines.
- Introduce a **Publishing Engine** that orchestrates publishing pipelines without containing business logic.
- Define plugin ports for project understanding, strategy, document planning, document generation, and export.
- Ensure every published asset is traceable to its source evidence.
- Support incremental publishing: re-plan, re-generate, and re-export only what changed.

## Principles

- **No hardcoded documents.** The core does not contain a fixed list of files such as `README.md`, `PRD.md`, or `API.md`. Document kinds are contributed by plugins and configuration.
- **No hardcoded folders.** Output locations are chosen by exporters from a target spec, not hardwired into the engine.
- **Project-type agnostic.** Project profiles are inferred from evidence, not assumed.
- **Output-format agnostic.** The core produces structured `GeneratedDocument` objects; exporters serialize to Markdown, JSON, HTML, DOCX, PDF, AI context bundles, etc.
- **Plugin-oriented.** All document-kind definitions, strategy heuristics, generators, and exporters are plugins or configuration.
- **Source-first traceability.** Every paragraph, section, and knowledge claim carries a `SourceReference`.

## Architecture Overview

### Layers (Clean Architecture, inside-out)

| Layer | Modules | Responsibility |
|---|---|---|
| **Domain** | `akwb.domain.publishing` | `GeneratedDocument`, `PlannedDocument`, `PublishingManifest`, `ProjectUnderstanding`, `SourceReference`, ports. |
| **Application** | `akwb.engines.publishing` | `PublishingEngine`, `ProjectUnderstandingEngine`, `AdaptivePublishingStrategyEngine`, `DocumentPlanningEngine`, `PublishingRulesEngine`. |
| **Adapter** | `akwb.plugins.publishing.*`, `akwb.reporting` | `DocumentGenerator` plugins, `Exporter` plugins, `ProjectTypeDetector` plugins, `StrategyContributor` plugins. |
| **Infrastructure** | `akwb.storage`, `akwb.events`, `akwb.observability` | Persistence, event bus, structured logging. |

### Core Components

1. **Publishing Engine** — Orchestrates the entire pipeline.
2. **Project Understanding Engine** — Infers the project's nature, audience, and maturity from evidence.
3. **Knowledge Domain Model** — Defines and selects the relevant knowledge domains for the project.
4. **Adaptive Publishing Strategy Engine** — Decides *what* documents should exist and why.
5. **Document Planning Engine** — Produces a validated, ordered `DocumentPlan`.
6. **Publishing Rules Engine** — Applies rules for create, merge, split, update, version, and supersede.
7. **Document Generation Adapters** — `DocumentGenerator` plugins that turn a `PlannedDocument` and selected knowledge into a `GeneratedDocument`.
8. **Export Architecture** — `Exporter` plugins that serialize `GeneratedDocument`s and the `PublishingManifest` to target locations and formats.
9. **Traceability Model** — Captures source references for every content block.
10. **Publishing Manifest** — Canonical record of every planned, generated, and exported document.

## Data Flow

```
SourceCatalog + KnowledgeGraph + Memory
              ↓
    Project Understanding Engine
              ↓
    ProjectUnderstanding + DomainSelection
              ↓
    Adaptive Publishing Strategy Engine
              ↓
    DocumentCandidate[]
              ↓
    Publishing Rules Engine
              ↓
    DocumentPlanning Engine
              ↓
    DocumentPlan (PlannedDocument[])
              ↓
    DocumentGenerator plugins
              ↓
    GeneratedDocument[]
              ↓
    ExportEngine + Exporter plugins
              ↓
    Published artifacts + PublishingManifest
```

## Domain Events

- `PublishingStarted`
- `ProjectUnderstandingProduced`
- `KnowledgeDomainSelected`
- `PublishingStrategyProduced`
- `DocumentPlanned`
- `DocumentGenerated`
- `DocumentExported`
- `PublishingCompleted`
- `PublishingFailed` (with `Diagnostic`)

## Plugin Ports

| Port | Input | Output | Owner |
|---|---|---|---|
| `ProjectTypeDetector` | `ProjectContext` (source summary, manifests) | `ProjectTypeEvidence` (type, confidence, signals) | Project Understanding Engine |
| `DomainContributor` | `ProjectUnderstanding` | `DomainRelevance` (domain id, confidence, rationale) | Knowledge Domain Model |
| `StrategyContributor` | `ProjectUnderstanding`, `DomainSelection`, `KnowledgeObjectCatalog` | `DocumentCandidate[]` | Adaptive Publishing Strategy Engine |
| `PublishingRule` | `DocumentCandidate`, existing `PublishingManifest` | `DocumentCandidate[]` (merged/split/updated) | Publishing Rules Engine |
| `DocumentPlanner` | `DocumentCandidate[]`, dependencies | `DocumentPlan` | Document Planning Engine |
| `DocumentGenerator` | `PlannedDocument`, knowledge sources | `GeneratedDocument` | Publishing Engine |
| `Exporter` | `ExportPackage` (documents + manifest) | `ExportResult` | Export Engine |
| `TraceabilityEnricher` | `GeneratedDocument` content block | `SourceReference[]` | Traceability Model (optional) |

## Inputs

- `SourceCatalog` from Discovery Engine.
- `KnowledgeGraph` from Knowledge / Graph Engines.
- `Memory` artifacts (facts, summaries) from Memory Engine.
- AI context (optional) from AI Context Engine.
- Effective configuration and plugin registry.
- Prior `PublishingManifest` for incremental publishing.

## Outputs

- `PublishingManifest` (canonical document inventory).
- `GeneratedDocument` stream (intermediate, before export).
- Exported artifacts via `Exporter` plugins.
- Domain events and diagnostics.

## Publishing Data Model (Summary)

This section summarizes the new value objects and aggregates introduced by the Publishing Architecture. Concrete schemas are defined in the domain layer during implementation.

### `DocumentKind` (Plugin-Contributed)

```json
{
  "id": "com.example.kind.architecture_decision_record",
  "name": "Architecture Decision Record",
  "description": "Records a significant architectural decision.",
  "required_knowledge_selectors": [
    {"kind": "knowledge_unit", "filter": "adr"},
    {"kind": "source", "path_glob": "adr/*.md"}
  ],
  "typical_audiences": ["technical"],
  "typical_domains": ["akwb.domain.architecture"],
  "default_generator_id": "com.example.generator.adr",
  "version": "1"
}
```

### `PlannedDocument`

```json
{
  "id": "plan://my-project/adr-index",
  "document_kind": "com.example.kind.architecture_decision_record",
  "purpose": "Summarize all architecture decision records.",
  "target_audience": "technical",
  "knowledge_sources": [
    {"id": "source://markdown/adr/001-api.md", "kind": "markdown"}
  ],
  "dependencies": ["plan://my-project/adr-001"],
  "confidence": 0.92,
  "priority": 80,
  "status": "planned",
  "owner": "com.example.strategy.software",
  "domain_tags": ["akwb.domain.architecture"],
  "publishing_order": 3,
  "regenerate": true,
  "version_of": null,
  "supersedes": null,
  "merge_of": [],
  "split_from": null
}
```

### `GeneratedDocument`

```json
{
  "id": "gen://my-project/adr-index",
  "planned_document_id": "plan://my-project/adr-index",
  "document_kind": "com.example.kind.architecture_decision_record",
  "title": "Architecture Decision Records",
  "blocks": [
    {
      "id": "b1",
      "content_type": "heading",
      "content": "Architecture Decision Records",
      "provenance": {
        "source_refs": ["source://markdown/adr/001-api.md"],
        "generated_by": "com.example.generator.adr",
        "generated_at": "2026-07-27T12:00:00Z",
        "transformations": ["summarize"]
      }
    }
  ],
  "domain_tags": ["akwb.domain.architecture"],
  "diagnostics": []
}
```

### `PublishingManifest`

```json
{
  "schema_version": "publishing-manifest-v1",
  "project_id": "/path/to/project",
  "created_at": "2026-07-27T12:00:00Z",
  "plan_id": "plan:uuid",
  "documents": [
    {
      "planned_id": "plan://my-project/adr-index",
      "generated_id": "gen://my-project/adr-index",
      "status": "generated",
      "export_records": [
        {"target": {"target_type": "workspace"}, "path": "reports/adr-index.md", "fingerprint": "sha256:..."}
      ]
    }
  ],
  "diagnostics": []
}
```

### `ExportPackage`

```json
{
  "package_id": "pkg:uuid",
  "target": {
    "target_type": "local_path",
    "uri": "docs/",
    "format": "markdown",
    "options": {"toc": true}
  },
  "documents": ["gen://my-project/adr-index"],
  "manifest": {"schema_version": "publishing-manifest-v1"}
}
```

## Publishing Rules as a Distinct Stage

The `PublishingRulesEngine` runs between the `AdaptivePublishingStrategyEngine` and the `DocumentPlanningEngine`. It applies rules for create, merge, split, update, version, and supersede before the planner builds the dependency graph. This keeps strategy focused on *what* documents are needed and planning focused on *when* and *how* to generate them.

## Dependencies

- `../03_SYSTEM_ARCHITECTURE.md`
- `../04_DOMAIN_MODEL.md`
- `../06_PLUGIN_ARCHITECTURE.md`
- `../08_KNOWLEDGE_ENGINE.md`
- `../11_DATA_MODEL.md`
- `PROJECT_UNDERSTANDING_ENGINE.md`
- `KNOWLEDGE_DOMAIN_MODEL.md`
- `ADAPTIVE_PUBLISHING_STRATEGY.md`
- `DOCUMENT_PLANNING_ENGINE.md`
- `EXPORT_ARCHITECTURE.md`
- `TRACEABILITY_MODEL.md`

## Future Extensions

- Multi-project publication aggregation.
- Publication workflows with approval gates.
- Scheduled / CI publishing triggers.
- Remote publication targets (Confluence, SharePoint, GitHub Pages).

## Risks

- Strategy plugins may disagree; conflict resolution must be deterministic.
- Over-abstraction can make simple projects harder to configure.
- Traceability at paragraph granularity may bloat storage if not normalized.

## Design Decisions

- The **Publishing Engine** is a new application-layer orchestrator, not a replacement for the **Workspace Engine**. The Workspace Engine owns persistence and two-phase commit; the Publishing Engine owns document planning and generation.
- Document kinds are contributed by plugins through a `DocumentKind` registry; the core engine only reasons about abstract `PlannedDocument` and `GeneratedDocument` objects.
- Exporters are first-class plugin ports; no output format is privileged in core.
- Traceability is a cross-cutting domain model, not an engine; every content block carries `SourceReference`s.
- Incremental publishing re-uses the `ArtifactManifest` / `PublishingManifest` diff pattern already established by the Incremental Engine.
