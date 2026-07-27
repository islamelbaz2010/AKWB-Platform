# Publishing Architecture Review

## Scope

This review evaluates the Sprint 3 Publishing Architecture documents for:
- Domain-Driven Design (DDD) and Clean Architecture alignment.
- SOLID principles and separation of concerns.
- Plugin orientation and project-type/output-format agnosticism.
- Absence of hardcoded documents, templates, and folders.
- Traceability and incremental behavior.
- Future-proofing and scalability.

## Overall Assessment

The Publishing Architecture provides a coherent, plugin-driven, adaptive publishing system that converts analyzed project knowledge into project-specific documents. It respects the existing Clean Architecture/DDD foundation and does not hardcode document structures or output locations.

## Strengths

1. **Adaptive by design.** Project understanding, domain selection, strategy, and planning are plugin-driven and evidence-based.
2. **No hardcoded documents/folders.** Document kinds, domains, and export targets are contributed by plugins and configuration.
3. **Clear separation of concerns.**
   - `ProjectUnderstandingEngine` infers project nature.
   - `KnowledgeDomainModel` selects relevant knowledge domains.
   - `AdaptivePublishingStrategyEngine` proposes document candidates.
   - `PublishingRulesEngine` applies create/merge/split/update/version/supersede rules.
   - `DocumentPlanningEngine` produces an ordered, validated plan.
   - `ExportEngine` delegates serialization to `Exporter` plugins.
4. **Traceability-first.** Every content block carries `Provenance` and `SourceReference`s; source kinds are registry-based.
5. **Incremental pipeline.** Each stage declares invalidation triggers and uses the existing `PublishingManifest` diff pattern.
6. **Output-format agnostic.** `GeneratedDocument` is decoupled from Markdown, HTML, DOCX, PDF, etc.
7. **Aligned with Freeze v1.** The architecture extends the seven-engine model by adding publishing-specific engines without violating the dependency rule or plugin extensibility model.

## Weaknesses Identified and Improvements Applied

### 1. Pipeline stages were missing a dedicated `PublishingRulesEngine` step

**Weakness:** `ADAPTIVE_PUBLISHING_STRATEGY.md` and `DOCUMENT_PLANNING_ENGINE.md` both described publishing-rule logic, causing duplicated responsibility.

**Improvement applied:**
- Added `PublishingRulesEngine` as a distinct pipeline stage in `PUBLISHING_PIPELINE.md`.
- Removed rule application from the strategy engine; strategy now emits scored candidates.
- Removed rule application from document planning; planning now consumes already-transformed candidates.
- Added `PublishingRulesApplied` event to the pipeline event list.

### 2. Exporter I/O boundaries were ambiguous

**Weakness:** `EXPORT_ARCHITECTURE.md` stated that core never writes files and that exporters request writes through `StoragePort`, but `StoragePort` is sandboxed inside `.akwb/`. Exporters targeting `docs/` or external systems could not use it.

**Improvement applied:**
- Clarified that exporters perform their own I/O outside the `StoragePort` for non-workspace targets (`local_path`, `s3`, `api`, `stdout`).
- `StoragePort` is used only for `target_type=workspace`.
- Added `ExportTargetSpec` to formalize exporter capability declarations.
- Documented target resolution order with URI semantics.

### 3. New domain objects lacked a canonical data-model summary

**Weakness:** `DocumentCandidate`, `PlannedDocument`, `GeneratedDocument`, `PublishingManifest`, and `ExportPackage` schemas were spread across documents and inconsistent.

**Improvement applied:**
- Added a `Publishing Data Model (Summary)` appendix to `PUBLISHING_ARCHITECTURE.md` with JSON schemas for `DocumentKind`, `PlannedDocument`, `GeneratedDocument`, `PublishingManifest`, and `ExportPackage`.
- Aligned `DocumentCandidate` and `PlannedDocument` field names across `ADAPTIVE_PUBLISHING_STRATEGY.md` and `DOCUMENT_PLANNING_ENGINE.md` (`regenerate`, `version_of`, `status`).

### 4. `ProjectUnderstanding` and `Discovery Detector` overlap was unclear

**Weakness:** It was not obvious how project-type detection differs from Discovery's file/language classification.

**Improvement applied:**
- Added a `Relationship to Discovery Engine` section to `PROJECT_UNDERSTANDING_ENGINE.md`.
- Clarified that Discovery classifies files; Project Understanding consumes that catalog to infer holistic project nature.
- Documented that the engine is read-only with respect to Discovery output.

### 5. `DocumentPlanningEngine` process list still referenced rule application

**Weakness:** After splitting `PublishingRulesEngine` into its own stage, the planning process still described applying rules.

**Improvement applied:**
- Rewrote the `DocumentPlanningEngine` process to focus on deduplication, dependency resolution, scoring, topological sort, and validation.
- Added `regenerate` and `version_of` fields to `PlannedDocument`.

### 6. Publishing Architecture introduces new engines while Freeze v1 restricts them

**Weakness:** Architecture Freeze v1 says new engines require Architecture v2.

**Improvement applied:**
- `PUBLISHING_ARCHITECTURE.md` and `READY_FOR_IMPLEMENTATION.md` explicitly frame the publishing engines as an **Architecture v1.1 Publishing Extension** that requires approval.
- The engines are additive and do not alter existing Discovery, Knowledge, Graph, Memory, AI, Workspace, or Incremental engines.

### 7. Source traceability for AI-generated content needed stronger provenance rules

**Weakness:** `TRACEABILITY_MODEL.md` described source references but did not clearly require AI model attribution.

**Improvement applied:**
- Added `generated_by` and `transformations` fields to `Provenance`.
- Specified that AI-generated `ContentBlock`s must still cite original knowledge sources; the model is recorded in `generated_by`.
- Added `SourceConnector` and `TraceabilityEnricher` plugin ports for future external sources.

### 8. `KnowledgeDomain` examples could be mistaken for hardcoded taxonomy

**Weakness:** The example domain table might be read as a built-in list.

**Improvement applied:**
- Rephrased the table in `KNOWLEDGE_DOMAIN_MODEL.md` as *plugin-contributed default examples*.
- Added strong language that core only knows the `KnowledgeDomain` abstraction and that definitions live outside core.

## Remaining Open Questions

The following should be resolved during implementation, not in architecture:

1. Exact shape of `StrategyContext` knowledge selectors (query DSL vs. simple filters).
2. Whether `GeneratedDocument` content is one large text or a stream of `ContentBlock`s.
3. Whether `ExportEngine` belongs under `akwb.engines.publishing` or as a sibling `akwb.engines.export`.
4. Packaging of default `KnowledgeDomain` definitions (separate plugin vs. built-in config).
5. Concrete `PublishingManifest` diff algorithm and `regenerate` propagation details.
6. `DocumentGenerator` plugin contract: single call per planned document or batched.

## Conclusion

The Publishing Architecture is ready to guide implementation. The identified weaknesses were resolved by clarifying boundaries, adding a canonical data model, formalizing plugin ports, and ensuring the design is truly project-type and output-format agnostic.

## Recommendation

Approve as **Architecture v1.1 Publishing Extension** and proceed to a Foundation Sprint for the `akwb.engines.publishing` module and its domain models.
