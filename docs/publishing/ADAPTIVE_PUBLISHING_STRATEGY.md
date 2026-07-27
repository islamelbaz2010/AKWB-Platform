# Adaptive Publishing Strategy

## Purpose

Define how AKWB decides **what documents should exist** for an analyzed project. The strategy engine answers the question *"What needs to be published?"* but never dictates *how* documents are written or *where* they are stored.

## Responsibilities

- Consume `ProjectUnderstanding`, `DomainSelection`, and `KnowledgeObjectCatalog`.
- Run `StrategyContributor` plugins that propose `DocumentCandidate`s based on evidence.
- Aggregate, score, and filter candidates.
- Produce a `PublishingStrategy` (an ordered `DocumentCandidate[]`) for the `PublishingRulesEngine`.

## Principles

- **Decide what, not how.** Strategy produces candidates; generators and exporters decide rendering and location.
- **No hardcoded document lists.** The core has no built-in requirement to produce a `README.md` or `PRD.md`. Document kinds are plugin-contributed.
- **Evidence-driven.** Every candidate must cite the project understanding, domains, and knowledge objects that justify it.
- **Multi-domain.** A mixed project receives candidates from all active domains.
- **Configurable and overridable.** Users can force, suppress, or re-score candidates through configuration.

## Core Concepts

### `DocumentCandidate`

A proposed document that has not yet been validated or scheduled.

| Field | Meaning |
|---|---|
| `id` | Stable identifier (hash of kind + scope + key sources). |
| `document_kind` | Plugin-contributed `DocumentKind` id. |
| `purpose` | Why this document is needed. |
| `target_audience` | Intended readers. |
| `knowledge_sources` | `SourceReference`s and `KnowledgeObject` selectors. |
| `dependencies` | Candidate ids that should be generated first. |
| `confidence` | 0.0–1.0. |
| `priority` | Scheduling weight. |
| `regenerate` | Whether the candidate must be re-generated (`true`/`false`/`auto`). |
| `domain_tags` | Domains that justify the candidate. |
| `scope` | What part of the project the document covers (e.g., project-wide, a domain, a component). |
| `rationale` | Human-readable explanation from the strategy contributor. |
| `owner` | Contributing plugin id. |

### `StrategyContext`

| Field | Meaning |
|---|---|
| `project_understanding` | Inferred project profile. |
| `domain_selection` | Active knowledge domains. |
| `knowledge_objects` | Normalized knowledge catalog. |
| `previous_manifest` | Prior `PublishingManifest` for incremental decisions. |
| `config` | Effective configuration. |

### `StrategyResult`

| Field | Meaning |
|---|---|
| `contributor_id` | Plugin id. |
| `candidates` | `DocumentCandidate[]`. |
| `diagnostics` | Warnings or low-confidence notes. |

### `PublishingStrategy`

The aggregated output: a scored, deduplicated, and filtered list of candidates.

| Field | Meaning |
|---|---|
| `candidates` | `DocumentCandidate[]`. |
| `discarded` | Candidates removed with rationale. |
| `scored_by` | Configuration keys used for scoring (for reproducibility). |

## StrategyContributor Plugin Port

```python
class StrategyContributor(ABC):
    port_name: str = "strategy_contributor"

    @abstractmethod
    def contribute(
        self,
        context: StrategyContext,
    ) -> StrategyResult:
        """Return document candidates for the current project."""
        ...
```

## Strategy Process

1. **Collect strategy contributions.**
   - For each `StrategyContributor` plugin, build `StrategyContext` and call `contribute()`.
   - Contributors may produce zero, one, or many candidates.

2. **Normalize candidates.**
   - Validate that `document_kind` is registered.
   - Ensure every candidate has a `purpose`, `target_audience`, and `knowledge_sources`.
   - Resolve relative references in `knowledge_sources`.

3. **Deduplicate.**
   - Group by stable `id`.
   - Merge duplicates by combining `knowledge_sources` and taking the highest confidence.
   - If two contributors propose the same candidate with different priorities, core uses contributor priority from configuration or plugin manifest.

4. **Score and filter.**
   - Compute a final score from `confidence`, `priority`, `domain_confidence`, and `audience_urgency` (configurable weighting).
   - Drop candidates below `publishing.strategy_confidence_threshold`.

5. **Emit `PublishingStrategyProduced` event.**

## Confidence Scoring

Default scoring function (overridable by configuration):

```
final_score = (
    confidence * w1 +
    priority * w2 +
    domain_confidence * w3 +
    audience_urgency * w4
) / (w1 + w2 + w3 + w4)
```

Weights default to 1.0 and are normalized. Scores are clamped to [0.0, 1.0].

## Candidate Scoring

The final score is computed from candidate `confidence`, `priority`, `domain_confidence`, and `audience_urgency` using configurable weights. The `regenerate` flag is set based on the prior `PublishingManifest`:

- `regenerate=false` when a matching candidate exists, sources are unchanged, and `document_kind` has not changed.
- `regenerate=true` when sources, domain selection, or `document_kind` changed.
- `regenerate=auto` when the engine cannot determine safety (conservative default: re-generate).

## Incremental Strategy

- Load the prior `PublishingManifest`.
- For each candidate, check if a matching `PublishedDocument` exists.
- If sources and confidence are unchanged, mark `regenerate=false`.
- If `document_kind` definition changed, mark `regenerate=true` and `action=update`.
- If dependencies changed, propagate `regenerate=true` transitively.
- Removed candidates become `deletion` entries for the export stage.

## Inputs

- `ProjectUnderstanding`
- `DomainSelection`
- `KnowledgeObjectCatalog`
- Prior `PublishingManifest`
- Effective configuration
- `StrategyContributor` plugins

## Outputs

- `PublishingStrategy` containing `DocumentCandidate[]`.
- `PublishingStrategyProduced` domain event.
- Diagnostics for suppressed or low-confidence candidates.

## Future Extensions

- Interactive strategy review (CLI/UI) before planning.
- Machine-learning-based re-ranking from user feedback.
- Cross-project strategy templates shared through plugins.
- A/B testing document plans.

## Risks

- Multiple plugins may propose conflicting or redundant candidates.
- Overly aggressive default contributors can produce too many documents.
- Low confidence defaults may generate noise for ambiguous projects.

## Design Decisions

- **Strategy is a pure decision engine.** It does not read templates, write files, or call AI generation.
- **All document kinds are plugin-contributed.** The core only validates and scores.
- **Rule order is explicit and configurable.** This makes strategy behavior auditable.
- **Incremental strategy reuses the `PublishingManifest` diff pattern** already established by the Incremental Engine.
- **User overrides are first-class configuration:** `publishing.force_documents`, `publishing.suppress_documents`, `publishing.strategy_weights`.
