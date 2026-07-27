# Publishing Pipeline

## Purpose

Define the end-to-end pipeline that turns discovered knowledge objects into a structured, publishable output. The pipeline is **orchestrated**, not hardcoded: every stage delegates to plugins, configuration, or existing engines.

## Responsibilities

- Sequence the publishing stages from knowledge ingestion to exported artifacts.
- Coordinate existing engines (Discovery, Knowledge, Graph, Memory, AI, Incremental) and new publishing engines.
- Define stage inputs, outputs, events, and invalidation rules.
- Support incremental re-runs where only changed stages re-execute.
- Surface diagnostics and fail-soft behavior.

## Pipeline Stages

```
Knowledge Objects
        ↓
Knowledge Classification
        ↓
Project Understanding
        ↓
Publishing Strategy
        ↓
Publishing Rules
        ↓
Document Planning
        ↓
Document Generation
        ↓
Output Export
```

### 1. Knowledge Objects

**Input:** `SourceCatalog`, `KnowledgeGraph`, `Memory` artifacts.

**Process:**
- Normalize discovered sources, extracted knowledge units, relationships, and facts into a common `KnowledgeObject` view.
- Attach metadata: domain tags, source references, confidence, timestamps, content summaries.

**Output:** `KnowledgeObjectCatalog`.

**Owner:** Publishing Engine (adapter view over Discovery/Knowledge/Graph/Memory engines).

### 2. Knowledge Classification

**Input:** `KnowledgeObjectCatalog`.

**Process:**
- Apply `KnowledgeClassifier` plugins to label objects by role (`requirement`, `design`, `implementation`, `test`, `decision`, `risk`, `assumption`, etc.).
- Classifiers are lightweight; they do not parse syntax. They use tags, paths, names, and existing `KnowledgeUnit` kinds.

**Output:** `KnowledgeObjectCatalog` with `knowledge_role` and `content_type` annotations.

**Owner:** Publishing Engine with `KnowledgeClassifier` plugin port.

### 3. Project Understanding

**Input:** `KnowledgeObjectCatalog` and `SourceCatalog` summary.

**Process:**
- Run `ProjectTypeDetector` plugins.
- Aggregate `ProjectTypeEvidence` into `ProjectUnderstanding`.
- Infer audiences and maturity.

**Output:** `ProjectUnderstanding` value object.

**Owner:** `ProjectUnderstandingEngine`.

**Event:** `ProjectUnderstandingProduced`.

### 4. Knowledge Domain Selection

**Input:** `ProjectUnderstanding`, `KnowledgeObjectCatalog`.

**Process:**
- Load `KnowledgeDomain` definitions from plugins and configuration.
- Run `DomainContributor` plugins to score relevance.
- Produce `DomainSelection`.

**Output:** `DomainSelection` with active domains and object domain tags.

**Owner:** `KnowledgeDomainModel` + `DomainContributor` plugins.

**Event:** `KnowledgeDomainSelected`.

### 5. Publishing Strategy

**Input:** `ProjectUnderstanding`, `DomainSelection`, `KnowledgeObjectCatalog`.

**Process:**
- Run `StrategyContributor` plugins.
- Each contributor emits `DocumentCandidate`s based on evidence, not templates.
- Core aggregates, deduplicates, and scores candidates.

**Output:** `DocumentCandidate[]`.

**Owner:** `AdaptivePublishingStrategyEngine`.

**Event:** `PublishingStrategyProduced`.

### 6. Publishing Rules

**Input:** `DocumentCandidate[]`, prior `PublishingManifest`.

**Process:**
- Run `PublishingRule` plugins in configured order.
- Apply create, merge, split, update, version, supersede, defer, and discard decisions.
- Record `rationale` and lineage (`version_of`, `supersedes`, `merge_of`, `split_from`).

**Output:** Transformed `DocumentCandidate[]`.

**Owner:** `PublishingRulesEngine`.

**Event:** `PublishingRulesApplied`.

### 7. Document Planning

**Input:** `DocumentCandidate[]`.

**Process:**
- Deduplicate candidates.
- Resolve dependencies and build a directed graph; detect cycles.
- Score and prioritize candidates.
- Topologically sort candidates into `publishing_order`.
- Validate every `PlannedDocument` has knowledge sources and a target audience.
- Emit diagnostics for invalid or incomplete candidates.

**Output:** `DocumentPlan`.

**Owner:** `DocumentPlanningEngine`.

**Event:** `DocumentPlanProduced`.

### 8. Document Generation

**Input:** `DocumentPlan`, `KnowledgeObjectCatalog`.

**Process:**
- For each `PlannedDocument`, select a `DocumentGenerator` plugin by `document_kind`.
- Generator consumes the plan and knowledge sources and returns a `GeneratedDocument`.
- Traceability is attached to each content block.

**Output:** `GeneratedDocument[]`.

**Owner:** Publishing Engine + `DocumentGenerator` plugins.

**Event:** `DocumentGenerated` (per document).

### 9. Output Export

**Input:** `GeneratedDocument[]`, `PublishingManifest` (draft).

**Process:**
- `ExportEngine` groups documents into `ExportPackage`s by target.
- `Exporter` plugins serialize each package to the requested format and location.
- Exporters write artifacts and return `ExportResult`s.

**Output:** Exported artifacts, final `PublishingManifest`.

**Owner:** `ExportEngine` + `Exporter` plugins.

**Event:** `DocumentExported`.

## Incremental Pipeline

The Incremental Engine tracks pipeline stage state using fingerprints and manifest references.

| Stage | Invalidation Trigger |
|---|---|
| Knowledge Objects | Source catalog or knowledge graph changed. |
| Knowledge Classification | Classifier plugin version or configuration changed. |
| Project Understanding | Source catalog or detector plugin changed. |
| Domain Selection | Domain definitions or project understanding changed. |
| Publishing Strategy | Strategy plugins, domains, or project understanding changed. |
| Document Planning | Candidates, rules, or prior manifest changed. |
| Document Generation | Planned document, knowledge sources, or generator plugin changed. |
| Output Export | Generated document or exporter plugin changed. |

Each stage can be skipped if its inputs and plugins are unchanged. The `PublishingManifest` records which stage produced each artifact, enabling partial re-runs.

## Stage-to-Engine Mapping

| Stage | Engine / Component |
|---|---|
| Knowledge Objects | Discovery, Knowledge, Graph, Memory, AI Engines (read-only view) |
| Knowledge Classification | Publishing Engine + `KnowledgeClassifier` plugins |
| Project Understanding | `ProjectUnderstandingEngine` |
| Knowledge Domain Selection | `KnowledgeDomainModel` + `DomainContributor` plugins |
| Publishing Strategy | `AdaptivePublishingStrategyEngine` + `StrategyContributor` plugins |
| Document Planning | `DocumentPlanningEngine` + `PublishingRule` plugins |
| Document Generation | Publishing Engine + `DocumentGenerator` plugins |
| Output Export | `ExportEngine` + `Exporter` plugins |

## Plugin Ports Used by the Pipeline

| Port | Stage | Purpose |
|---|---|---|
| `KnowledgeClassifier` | Knowledge Classification | Label knowledge objects by role. |
| `ProjectTypeDetector` | Project Understanding | Infer project type from evidence. |
| `DomainContributor` | Knowledge Domain Selection | Contribute and score domains. |
| `StrategyContributor` | Publishing Strategy | Emit document candidates. |
| `PublishingRule` | Publishing Rules | Transform candidates (merge, split, version, etc.). |
| `DocumentPlanner` | Document Planning | Produce a validated, ordered plan. |
| `DocumentGenerator` | Document Generation | Generate content. |
| `Exporter` | Output Export | Serialize to target format/location. |
| `SourceConnector` | Traceability / Ingestion | Add future source kinds (optional). |

## Error Handling

- A failure in one stage does not abort the pipeline unless it is a structural prerequisite.
- `PublishingEngine` emits a `PublishingFailed` event with a `Diagnostic`.
- Partial documents and diagnostics are preserved in `PublishingManifest` so the user can inspect the state.
- `DocumentGenerator` failures result in a `GeneratedDocument` with `status=failed` and a diagnostic; dependent documents are deferred.

## Events

- `PublishingStarted`
- `KnowledgeObjectsPrepared`
- `KnowledgeClassified`
- `ProjectUnderstandingProduced`
- `KnowledgeDomainSelected`
- `PublishingStrategyProduced`
- `PublishingRulesApplied`
- `DocumentPlanProduced`
- `DocumentGenerated`
- `DocumentExported`
- `PublishingCompleted`
- `PublishingFailed`

## Inputs

- `SourceCatalog`
- `KnowledgeGraph`
- `Memory` artifacts
- `AI` context bundles (optional)
- `ProjectUnderstanding`
- `DomainSelection`
- `DocumentPlan`
- Prior `PublishingManifest`
- Plugin registry and configuration

## Outputs

- `GeneratedDocument[]`
- `ExportResult[]`
- `PublishingManifest`
- Diagnostics

## Dependencies

- `PUBLISHING_ARCHITECTURE.md`
- `PROJECT_UNDERSTANDING_ENGINE.md`
- `KNOWLEDGE_DOMAIN_MODEL.md`
- `ADAPTIVE_PUBLISHING_STRATEGY.md`
- `DOCUMENT_PLANNING_ENGINE.md`
- `EXPORT_ARCHITECTURE.md`
- `TRACEABILITY_MODEL.md`

## Future Extensions

- Parallel stage execution where dependencies allow.
- Conditional branches based on project profile or governance rules.
- Watch-mode pipeline triggered by file changes.
- Remote pipeline orchestration across workers.

## Risks

- A single slow generator can block the entire pipeline.
- Incorrect invalidation can skip necessary re-generation.
- Too many fine-grained events may hurt performance for large projects.

## Design Decisions

- **Pipeline stages are explicit value objects, not hidden functions.** Each stage publishes an event and a typed output, enabling observability and incremental replay.
- **No stage directly invokes another engine.** Orchestration happens through the `PublishingEngine` with events published to the `EventBus`.
- **Generators and exporters are plugin ports.** The core pipeline never contains Markdown/HTML/PDF logic.
- **Incremental invalidation is fingerprint-based**, reusing the existing `ArtifactManifest` and `SourceCatalog` diff approach.
