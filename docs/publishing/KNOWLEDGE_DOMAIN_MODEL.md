# Knowledge Domain Model

## Purpose

Define a **domain-driven, extensible model** for knowledge domains used during publishing. A knowledge domain is not a folder; it is a capability tag that describes *what kind of knowledge* a project contains and *what kind of documents* may be needed to express that knowledge.

## Responsibilities

- Provide a registry of abstract knowledge domains.
- Allow plugins and configuration to contribute domains, triggers, and default document kinds without modifying core.
- Map `ProjectUnderstanding` to a `DomainSelection`.
- Tag `KnowledgeObject`s and `PlannedDocument`s with domain membership.
- Support mixed projects where multiple domains are active simultaneously.

## Principles

- **No fixed taxonomy in core.** The core engine only understands the `KnowledgeDomain` abstraction.
- **Domains are not directories.** Output folder names are chosen by exporters, not by domain identity.
- **Plugin-driven registration.** Plugins and user configuration contribute domain definitions.
- **Multi-domain by default.** A source, knowledge unit, or document can belong to zero or more domains.

## Core Concepts

### `KnowledgeDomain`

A declaration of a knowledge area. Plugins contribute instances; the core registry validates uniqueness.

| Field | Meaning |
|---|---|
| `id` | Stable reverse-DNS identifier (`com.akwb.domain.engineering`). |
| `name` | Human-readable label (`Engineering`). |
| `description` | What the domain covers. |
| `triggers` | List of `DomainTrigger` conditions that make the domain relevant. |
| `priority` | Default ordering weight for strategy resolution. |
| `parent_domains` | Optional domain IDs this domain specializes. |
| `default_document_kinds` | Optional `DocumentKind` IDs that strategy contributors may emit. (Not hardcoded outputs; suggestions.) |
| `version` | Domain schema version. |

### `DomainTrigger`

A declarative condition that increases the relevance of a domain.

| Field | Meaning |
|---|---|
| `kind` | `project_type`, `source_kind`, `knowledge_unit_kind`, `file_pattern`, `manifest_key`, `audience`, `tag`. |
| `value` | Matched value or glob. |
| `weight` | Contribution to domain confidence. |

### `DomainRelevance`

A scored suggestion that a domain applies to the current project.

| Field | Meaning |
|---|---|
| `domain_id` | Domain identifier. |
| `confidence` | 0.0–1.0. |
| `signals` | `SourceReference`s and `Signal`s that triggered the relevance. |
| `contributor_id` | Plugin that produced the score. |

### `DomainSelection`

The set of active domains for the current publishing run.

| Field | Meaning |
|---|---|
| `selected_domains` | `DomainRelevance[]` above the confidence threshold. |
| `primary_domain` | Highest-confidence domain (optional). |
| `threshold` | Confidence cutoff used. |
| `excluded_domains` | Domains explicitly disabled by configuration. |

### `DomainTag`

A lightweight domain label attached to a `KnowledgeObject` or `PlannedDocument`.

```python
class DomainTag:
    domain_id: str
    confidence: float
    source_refs: list[SourceReference]
```

## Domain Registry

The `DomainRegistry` is an in-memory repository populated from:

1. Built-in **default domain definitions** shipped as plugin contributions (e.g., `akwb-publishing-defaults`).
2. Plugin contributions via the `DomainContributor` port.
3. Project configuration `publishing.domains`.
4. User global configuration `~/.config/akwb/publishing_domains.yaml`.

The core registry enforces:
- Unique `id`s.
- Acyclic `parent_domains` graph.
- Version compatibility.

## DomainContributor Plugin Port

```python
class DomainContributor(ABC):
    port_name: str = "domain_contributor"

    @abstractmethod
    def contribute_domains(self) -> list[KnowledgeDomain]:
        """Return domain definitions this plugin provides."""
        ...

    @abstractmethod
    def score_relevance(
        self,
        understanding: ProjectUnderstanding,
        context: DomainScoringContext,
    ) -> list[DomainRelevance]:
        """Return relevance scores for the domains this plugin owns."""
        ...
```

## Domain Selection Process

1. Load all `KnowledgeDomain` definitions into `DomainRegistry`.
2. For each `DomainContributor` plugin, call `score_relevance`.
3. Collect `DomainRelevance` objects.
4. Group by `domain_id` and aggregate confidence (configurable: max, weighted average, or sum with cap).
5. Filter out domains below `publishing.domain_confidence_threshold`.
6. Apply user `excluded_domains` and `forced_domains`.
7. Emit `KnowledgeDomainSelected` event with the final `DomainSelection`.

## Example Domains (Plugin-Contributed Defaults)

These are **illustrative** domain definitions, not hardcoded core behavior. They may be overridden, removed, or extended by plugins.

| Domain ID | Description | Typical Triggers |
|---|---|---|
| `akwb.domain.foundation` | Project setup, conventions, onboarding. | `README`, `CONTRIBUTING`, `LICENSE`, `.akwb/config.yaml` |
| `akwb.domain.business` | Business goals, stakeholders, requirements. | `business/`, `prd/`, `investment_memo*`, `stakeholder*`, `roadmap*` |
| `akwb.domain.architecture` | System design, components, interfaces. | `architecture/`, `adr/`, `api/`, `openapi*`, `schema/` |
| `akwb.domain.engineering` | Implementation details, code, tests. | `src/`, `tests/`, `package.json`, `pyproject.toml`, `Cargo.toml` |
| `akwb.domain.ai` | Model cards, prompts, AI behavior, agents. | `prompts/`, `ai/`, `models/`, `system_prompt*` |
| `akwb.domain.operations` | Runbooks, deployment, monitoring. | `ops/`, `deploy/`, `runbooks/`, `k8s/`, `terraform/` |
| `akwb.domain.marketing` | Brand, campaigns, messaging. | `marketing/`, `campaigns/`, `brand*`, `content/` |
| `akwb.domain.finance` | Financial analysis, budgets, valuation. | `finance/`, `budget*`, `valuation*`, `investment/` |
| `akwb.domain.compliance` | Regulations, audits, controls. | `compliance/`, `security/`, `gdpr*`, `hipaa*`, `soc2*` |
| `akwb.domain.memory` | Historical decisions, lessons, context. | `memory/`, `decisions/`, `lessons*`, `retrospectives/` |
| `akwb.domain.research` | Hypotheses, experiments, findings. | `experiments/`, `research/`, `hypotheses*`, `findings/` |
| `akwb.domain.strategy` | Goals, roadmaps, competitive positioning. | `strategy/`, `goals*`, `roadmap*`, `competitive*` |
| `akwb.domain.risk` | Risk register, mitigation plans. | `risk/`, `risk_register*`, `mitigation*` |
| `akwb.domain.governance` | Policies, roles, approvals. | `governance/`, `policies/`, `roles*`, `approvals/` |
| `akwb.domain.prompts` | Reusable prompt libraries. | `prompts/`, `prompts.json`, `system_prompt*` |
| `akwb.domain.automation` | Scripts, workflows, CI/CD. | `.github/`, `.gitlab-ci*`, `Makefile`, `scripts/` |
| `akwb.domain.media` | Images, videos, diagrams, audio. | `assets/`, `media/`, `images/`, `diagrams/` |

## Relationship to Knowledge Objects

- Every `KnowledgeObject` (source, unit, relationship, fact) can carry `domain_tags`.
- Domain tags are produced by `DomainContributor` plugins or by the `KnowledgeDomain` trigger rules applied to source metadata.
- Document strategy plugins can request "all knowledge objects tagged with `akwb.domain.compliance`" without knowing folder layouts.

## Relationship to Document Planning

- `PlannedDocument` carries a `domain_id` and `domain_confidence`.
- `DocumentPlanningEngine` uses domain tags to group, prioritize, and deduplicate candidates.
- A single document may be tagged with multiple domains when a strategy plugin explicitly emits a cross-domain candidate.

## Inputs

- `ProjectUnderstanding` from Project Understanding Engine.
- `KnowledgeObjectCatalog` from Knowledge / Graph Engines.
- Effective configuration and plugin registry.
- Existing `DomainSelection` (for incremental diff).

## Outputs

- `DomainSelection` value object.
- `KnowledgeObject` domain tags.
- `KnowledgeDomainSelected` domain event.
- Diagnostics for domain conflicts or missing definitions.

## Future Extensions

- Domain inheritance and specialization.
- Cross-project domain alignment.
- Domain-specific governance rules.
- Dynamic domain creation from user feedback.

## Risks

- Domain bloat: too many overlapping domains produce noisy document plans.
- Weak triggers can over-activate a domain.
- User configuration may disable all default domains and leave the strategy engine empty.

## Design Decisions

- **Core knows only `KnowledgeDomain`, `DomainTrigger`, `DomainRelevance`, and `DomainSelection`.** Concrete domain definitions live outside core.
- **Domain IDs are stable reverse-DNS strings** to avoid collisions between plugins.
- **Triggers are declarative and auditable.** A domain's activation can be explained by a list of `SourceReference`s.
- **Domain selection is recomputed each run.** The Incremental Engine diff compares selections and invalidates downstream documents when domains change.
