# Project Understanding Engine

## Purpose

Infer the **nature, audience, and maturity** of an analyzed project from discovered evidence. Project understanding is the first adaptive step in the publishing pipeline; it drives domain selection, publishing strategy, and document planning without hardcoding project assumptions.

## Responsibilities

- Consume `SourceCatalog`, `KnowledgeGraph`, and optional `Memory` artifacts.
- Collect **signals** from file presence, directory layouts, dependency manifests, documentation structure, and source-level metadata.
- Run `ProjectTypeDetector` plugins to produce `ProjectTypeEvidence`.
- Aggregate evidence into a ranked, multi-label `ProjectUnderstanding`.
- Infer **target audiences** and **maturity / governance level**.
- Expose confidence scores so downstream engines can decide when to request human confirmation or fall back to generic defaults.

## Principles

- **Evidence-based, not assumption-based.** A project is not typed by a single file extension; it is typed by a weighted collection of signals.
- **Multi-label by default.** A repository can be both a `software-platform` and a `research` project; it can also contain `marketing` or `finance` collateral.
- **Plugin-driven.** The core engine only aggregates; signal detection is performed by plugins.
- **No code parsing.** This engine does not parse source code semantics; it inspects catalog metadata, file paths, manifest contents, and `KnowledgeUnit` kinds at the surface level.
- **Layered on Discovery.** The Discovery Engine already classifies files by language/role. The Project Understanding Engine consumes that summary to infer higher-level project nature.

## Core Concepts

### `ProjectUnderstanding` (Aggregate / Value Object)

A read-only snapshot produced for each analysis run.

| Field | Meaning |
|---|---|
| `project_id` | Absolute or stable project identifier. |
| `primary_profile` | Highest-confidence `ProjectProfile`. |
| `profiles` | All `ProjectProfile`s with confidence above threshold. |
| `audiences` | Inferred readers (e.g., `technical`, `executive`, `regulatory`, `public`, `team`). |
| `maturity` | `prototype`, `active`, `stable`, `legacy`, or `unknown`. |
| `governance` | Hints from compliance files, security docs, review processes. |
| `signals` | Flat list of all evidence used, with provenance. |
| `confidence` | Overall confidence 0.0–1.0. |
| `missing_context` | List of signals the engine expected but did not find. |

### `ProjectProfile`

| Field | Meaning |
|---|---|
| `type` | Project-type label (`software-platform`, `investment`, `research`, `medical`, `legal`, `agency`, etc.). |
| `confidence` | 0.0–1.0. |
| `dominance` | Share of total signal weight contributed by this type. |
| `signals` | Source references that support the label. |

### `ProjectTypeEvidence`

| Field | Meaning |
|---|---|
| `type` | Proposed project-type label. |
| `confidence` | Per-detector confidence. |
| `weight` | Detector-reported weight (e.g., `strong`, `medium`, `weak`). |
| `signals` | List of `Signal` objects. |
| `detector_id` | Source plugin. |

### `Signal`

| Field | Meaning |
|---|---|
| `kind` | `file_presence`, `manifest_key`, `directory_layout`, `naming_convention`, `documentation_title`, `knowledge_unit_kind`, `config_value`. |
| `source_ref` | `SourceReference` to the artifact that produced the signal. |
| `value` | Normalized signal value (e.g., filename, key, title). |
| `weight` | Detector-assigned weight. |

## Process

1. **Collect signals.**
   - Iterate over `SourceCatalog` entries: file names, paths, MIME types, tags, classification.
   - Inspect manifest-like files (`package.json`, `pyproject.toml`, `pom.xml`, `Cargo.toml`, `investment_memo.yaml`, `clinical_trial_protocol.docx`, etc.).
   - Inspect directory structures (`src/`, `tests/`, `docs/`, `experiments/`, `campaigns/`, `protocols/`, `legal/`).
   - Read lightweight `KnowledgeUnit` kinds produced by Discovery or early Knowledge Engine (optional).

2. **Run `ProjectTypeDetector` plugins.**
   - Each detector receives a `ProjectContext` and returns `ProjectTypeEvidence`.
   - Core does not interpret signal semantics; it normalizes weights and merges evidence.

3. **Normalize and aggregate evidence.**
   - Group signals and evidence by project `type`.
   - Compute `ProjectProfile` confidence using a configurable weighted aggregation.
   - Mark a profile as dominant if its share exceeds a configurable threshold (default 0.5).

4. **Infer audiences and maturity.**
   - Audiences are derived from detected document patterns (e.g., `README` for `public`, `adr/` for `technical`, `executive_summary.md` for `executive`, `compliance/` for `regulatory`).
   - Maturity is derived from CI configs, changelog presence, version tags, test coverage, deprecation markers, and `KnowledgeUnit` stability metrics.

5. **Emit `ProjectUnderstandingProduced` event.**

## ProjectTypeDetector Plugin Port

```python
class ProjectTypeDetector(ABC):
    port_name: str = "project_type_detector"

    @abstractmethod
    def detect(self, context: ProjectContext) -> ProjectTypeEvidence:
        """Return evidence for one or more project types."""
        ...
```

### `ProjectContext` Input

```python
class ProjectContext:
    project_root: str
    source_catalog: SourceCatalogSummary  # paths, tags, classifications, counts
    manifest_snippets: list[ManifestSnippet]  # small key/value excerpts from manifest files
    top_level_directories: list[str]
    knowledge_unit_kinds: list[str]  # optional early summary
    existing_publishing_manifest: PublishingManifest | None
```

### `ProjectTypeEvidence` Output

```python
class ProjectTypeEvidence:
    detector_id: str
    project_types: list[ProjectTypeScore]
    signals: list[Signal]
    diagnostics: list[Diagnostic]
```

## Supported Project Types (Plugin-Contributed Examples)

These are **example labels** that plugins may register. The core engine has no built-in preference for any of them.

- `software-platform`
- `investment`
- `research`
- `medical`
- `legal`
- `construction`
- `education`
- `agency`
- `government`
- `non-profit`
- `startup`
- `internal-operations`

A project may receive multiple labels with non-zero confidence.

## Mixed Project Types

- The engine preserves **all** labels above a configurable `confidence_threshold`.
- The `primary_profile` is the label with highest dominance.
- Downstream strategy plugins receive the full `ProjectUnderstanding` and may emit document candidates for any relevant profile.
- Conflicting evidence is recorded as diagnostics; strategy plugins may disambiguate by domain or confidence.

## Inputs

- `SourceCatalog` from Discovery Engine.
- Optional `KnowledgeGraph` summary from Knowledge / Graph Engines.
- `Memory` artifacts (if available).
- Effective configuration: `publishing.project_type_detector_threshold`, `publishing.audience_inference`.

## Outputs

- `ProjectUnderstanding` value object.
- `ProjectUnderstandingProduced` domain event.
- Diagnostics for low-confidence or conflicting detections.

## Future Extensions

- Temporal project understanding across snapshots (trend analysis).
- Human-in-the-loop confirmation and feedback loop.
- Cross-project similarity detection.
- Fine-grained sub-type detection (`saas`, `library`, `firmware`, `clinical-study`, `grant-proposal`).

## Risks

- Weak signals can produce misleading primary profiles.
- Conflicting detectors need transparent, user-overridable resolution.
- Overfitting to default plugin signals may introduce hidden assumptions.

## Relationship to Discovery Engine

- Discovery Engine's `Detector` plugins classify individual files (language, role, MIME).
- Project Understanding Engine's `ProjectTypeDetector` plugins consume the aggregated `SourceCatalog` and `KnowledgeGraph` to infer holistic project type, audience, and maturity.
- There is no circular dependency: Project Understanding runs after Discovery and treats its output as read-only evidence.

## Design Decisions

- **Core is agnostic:** it does not know what a "software platform" looks like; only plugins do.
- **Evidence is first-class:** every profile score must cite `Signal`s and source references for auditability.
- **Confidence threshold is configurable** per project; low-confidence runs produce `missing_context` and broader document plans.
- **Project understanding is a value object**, not an entity; it is recomputed each analysis and compared to prior snapshots by the Incremental Engine.
