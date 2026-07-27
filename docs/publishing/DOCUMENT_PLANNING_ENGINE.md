# Document Planning Engine

## Purpose

Produce a **validated, ordered, and explainable plan** of documents to publish for the current project. The plan is the bridge between strategy ("what should exist") and generation ("write the content"). It contains no templates and no output-format assumptions.

## Responsibilities

- Consume `DocumentCandidate`s produced by the PublishingRulesEngine.
- Resolve dependencies between documents.
- Score, prioritize, and order candidates.
- Validate that every planned document has required knowledge sources and a target audience.
- Emit a `DocumentPlan` that the Publishing Engine can execute.

## Principles

- **Plan before generate.** No document generator is invoked until a stable plan exists.
- **No templates.** The plan describes *what* a document is for, not *how* it is laid out.
- **Dependency-aware.** Documents that feed into other documents are ordered first.
- **Incremental-friendly.** The plan diff against the prior `PublishingManifest` determines re-generation, not a full rebuild.

## Core Concepts

### `PlannedDocument` (Value Object)

| Field | Meaning |
|---|---|
| `id` | Stable identifier (derived from document kind + scope + project id). |
| `document_kind` | Reference to a `DocumentKind` definition (plugin-contributed). |
| `purpose` | Why this document exists. |
| `target_audience` | Primary audience (`technical`, `executive`, `regulatory`, `public`, `team`, custom). |
| `knowledge_sources` | `SourceReference`s and `KnowledgeObject` selectors used. |
| `dependencies` | IDs of `PlannedDocument`s that must be generated before this one. |
| `confidence` | 0.0–1.0 that this document is appropriate. |
| `priority` | Scheduling weight (lower = earlier). |
| `status` | `planned`, `merged`, `split`, `superseded`, `deferred`, `discarded`. |
| `regenerate` | `true`/`false`/`auto` — whether to re-generate this document. |
| `version_of` | Optional `id` this document is a new version of. |
| `owner` | Generating plugin or user override. |
| `domain_tags` | Associated knowledge domains. |
| `publishing_order` | Final topologically sorted position. |
| `merge_of` / `split_from` / `supersedes` | Lineage for version/supersede rules. |

### `DocumentPlan` (Aggregate)

| Field | Meaning |
|---|---|
| `plan_id` | UUID for this analysis run. |
| `project_id` | Project identifier. |
| `documents` | `PlannedDocument[]` in topological order. |
| `discarded` | Candidates removed with rationale. |
| `diagnostics` | Warnings/errors from validation. |
| `created_at` | ISO timestamp. |

### `DocumentKind` (Plugin-Contributed Definition)

A `DocumentKind` describes a class of documents without dictating template or output format.

| Field | Meaning |
|---|---|
| `id` | Stable reverse-DNS identifier. |
| `name` | Human label. |
| `required_knowledge_selectors` | What knowledge objects/sources are needed. |
| `typical_audiences` | Suggested audiences (not enforced). |
| `typical_domains` | Suggested domains (not enforced). |
| `generator_plugin_id` | Default `DocumentGenerator` plugin. |

## Process

1. **Collect candidates.** Receive `DocumentCandidate[]` from `PublishingRulesEngine`.
2. **Deduplicate.** Compare `id` and `document_kind` + scope. Collapse duplicates using confidence and plugin priority.
3. **Resolve dependencies.** Build a directed graph from `dependencies`. Detect cycles and emit diagnostics.
4. **Score and prioritize.** Combine confidence, priority, audience urgency, and domain relevance. Preserve `regenerate` flags from upstream rules.
5. **Topological sort.** Produce `publishing_order` respecting dependencies.
6. **Validate.** Ensure every planned document has a non-empty `knowledge_sources` list and a `target_audience`. Emit diagnostics for failures.
7. **Emit `DocumentPlanProduced` event.**

## DocumentPlanner Plugin Port

```python
class DocumentPlanner(ABC):
    port_name: str = "document_planner"

    @abstractmethod
    def plan(
        self,
        candidates: list[DocumentCandidate],
        context: DocumentPlanningContext,
    ) -> DocumentPlan:
        """Return an ordered, validated document plan."""
        ...
```

### `DocumentPlanningContext`

```python
class DocumentPlanningContext:
    project_understanding: ProjectUnderstanding
    domain_selection: DomainSelection
    knowledge_objects: KnowledgeObjectCatalog
    previous_manifest: PublishingManifest | None
    config: dict
```

## Publishing Rules Engine

The `PublishingRulesEngine` is a pipeline of `PublishingRule` plugins. Each rule receives the current candidate and the prior manifest and may transform it.

```python
class PublishingRule(ABC):
    port_name: str = "publishing_rule"

    @abstractmethod
    def apply(
        self,
        candidate: DocumentCandidate,
        previous_manifest: PublishingManifest | None,
        context: DocumentPlanningContext,
    ) -> PublishingRuleResult:
        ...
```

### `PublishingRuleResult`

| Field | Meaning |
|---|---|
| `action` | `create`, `merge`, `split`, `update`, `version`, `supersede`, `defer`, `discard`. |
| `documents` | Resulting `DocumentCandidate`/`PlannedDocument` objects. |
| `rationale` | Human-readable explanation. |
| `diagnostics` | Optional warnings. |

## Plan Validation Rules

- `knowledge_sources` must not be empty.
- `target_audience` must be present and from the allowed audience vocabulary or a custom value.
- `purpose` must be non-empty.
- Dependency graph must be acyclic.
- Every `document_kind` must be registered in the `DocumentKindRegistry`.
- `priority` must be a finite number (NaN/inf rejected).

## Incremental Planning

- Load prior `PublishingManifest`.
- Compare planned documents by stable `id`.
- Mark unchanged documents with `status=planned` and `regenerate=false` if knowledge sources and confidence are stable.
- Mark documents whose sources changed as `update`.
- Mark documents whose kind/domain changed as `supersede` or `version`.
- Remove documents whose sources no longer exist.

## Inputs

- `DocumentCandidate[]` from `PublishingRulesEngine`.
- `ProjectUnderstanding`.
- `DomainSelection`.
- `KnowledgeObjectCatalog`.
- Prior `PublishingManifest`.
- Effective configuration.

## Outputs

- `DocumentPlan` aggregate.
- `DocumentPlanProduced` domain event.
- Diagnostics.

## Future Extensions

- Interactive plan approval (CLI/UI).
- Plan optimization for token budgets, page counts, or reading time.
- Multi-language publication planning.
- Conditional plans based on review workflows.

## Risks

- Cyclic dependencies block the plan if not detected.
- Too many candidates produce an unwieldy plan.
- `PublishingRule` plugins may conflict; order and priority must be deterministic.

## Design Decisions

- **The engine does not generate content.** It only produces a validated, ordered plan.
- **Document kinds are plugin-contributed.** The core validates but does not define them.
- **Topologically sorted order is explicit.** Generators can rely on `publishing_order` when consuming upstream documents.
- **Lineage fields (`merge_of`, `split_from`, `supersedes`) preserve provenance** for incremental updates and audit trails.
- **Validation failures are diagnostics, not exceptions.** A partial plan is emitted so the user can inspect what was rejected and why.
