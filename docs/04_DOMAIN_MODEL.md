# Domain Model

## Purpose
Define the core domain concepts, aggregates, entities, value objects, and ubiquitous language used across AKWB.

## Responsibilities
- Establish a shared vocabulary.
- Define bounded contexts, aggregate roots, and invariants.
- Catalog domain events.
- Provide a reference for the data model, engines, and plugin contracts.

## Bounded Contexts
1. **Project Context:** The analyzed software project and its snapshots over time.
2. **Source Context:** Files, documents, and their classification.
3. **Knowledge Context:** Extracted entities, relationships, and traceability.
4. **Workspace Context:** Generated artifacts, indexes, memory, and graph exports.
5. **AI Context:** Context bundles, embeddings, and summaries optimized for LLMs.

## Core Aggregates and Entities

### Project (Aggregate Root)
- `id`: canonical project path.
- `rootPath`: absolute filesystem root.
- `detectedProfiles`: list of detected language/framework profiles.
- `configurationRef`: reference to effective configuration snapshot.
- `lastAnalysisAt`: timestamp of last successful analysis.
- `snapshotRefs`: references to historical snapshots.

### Snapshot (Entity)
- `id`: content-addressable snapshot identifier.
- `createdAt`: timestamp.
- `sourceCatalogRef`: reference to `SourceCatalog`.
- `knowledgeGraphRef`: reference to `KnowledgeGraph`.
- `artifactManifestRef`: reference to `ArtifactManifest`.
- `parentSnapshotId`: previous snapshot for incremental diff.

### SourceCatalog (Aggregate Root)
- `projectId`
- `sourceEntries`: list of `SourceEntry` entities.
- `detectorMetadata`: which detectors ran and their confidence scores.
- `classificationSummary`: counts by language and role.

### SourceEntry (Entity)
- `relativePath`: project-relative path.
- `absolutePath`: resolved absolute path.
- `fingerprint`: content hash, size, and mtime.
- `language`, `role`, `mimeType`, `tags`
- `detectorId`: detector that classified the source.
- `parserHint`: preferred parser plugin id.
- `encoding`

### KnowledgeGraph (Aggregate Root)
- `projectId`
- `version`
- `nodes`: `KnowledgeUnit` entities.
- `edges`: `Relationship` entities.
- `statistics`: counts and coverage metrics.

### KnowledgeUnit (Entity)
- `id`: stable URI based on project-relative locator.
- `kind`: module, class, function, service, API, variable, concept, doc, etc.
- `name`, `qualifiedName`, `displayName`
- `sourceRefs`: source path spans.
- `properties`: typed key/value map.
- `summary`: natural-language summary.
- `embeddingRef`: optional reference to pre-computed embedding.

### Relationship (Entity)
- `id`
- `sourceId`, `targetId`: knowledge unit ids.
- `kind`: imports, calls, implements, references, depends_on, tests, documents, contains, etc.
- `confidence`: 0.0–1.0.
- `evidence`: source path and span where the relationship was observed.
- `properties`

### Artifact (Entity)
- `id`
- `kind`: report, context_bundle, graph_export, memory_dump, index, embedding, etc.
- `sourceRefs`: inputs that produced the artifact.
- `contentRef`: path or storage key to the artifact file.
- `fingerprint`
- `createdAt`

## Domain Events
- `ProjectOpened`
- `SourceDiscovered`
- `SourceClassified`
- `KnowledgeExtracted`
- `RelationshipInferred`
- `ArtifactProduced`
- `WorkspaceSealed`
- `ContextRequested`

## Inputs
- Product vision and requirements.
- Language and framework domain knowledge.
- Plugin port contracts.

## Outputs
- Ubiquitous language glossary.
- Aggregate boundaries and invariants.
- Domain event catalog.

## Dependencies
- `01_PRODUCT_VISION.md`
- `02_PRODUCT_REQUIREMENTS.md`

## Future Extensions
- Multi-project relationships and cross-repository graphs.
- Time-series snapshots and workspace versioning.
- Semantic concepts imported from external ontologies.

## Risks
- Over-normalization can hurt performance; aggregate boundaries balance correctness and speed.
- Stable IDs across file renames require heuristics that may fail.

## Design Decisions

- Define repository interfaces in the domain layer: `ProjectRepository`, `SourceCatalogRepository`, `KnowledgeGraphRepository`, `ArtifactRepository`, `SnapshotRepository`, `ConfigRepository`.
- Add `ArtifactManifest` as a first-class aggregate that tracks artifact lineage and invalidation.
- Model `Package` and `Dependency` entities so dependency manifests can participate in the knowledge graph.
- Introduce `Result<T, Diagnostic>` and `Diagnostic` value objects to represent partial failures without crashing analysis.
- Add an `IdentityResolver` domain service for merging duplicate `KnowledgeUnit`s produced by multiple extractors.
- Add domain events: `AnalysisStarted`, `AnalysisCompleted`, `DiagnosticReported`, `ArtifactInvalidated`.
- Project-relative URIs are stable identifiers for source-derived knowledge units.
- Relationships carry confidence and evidence to support uncertain or inferred links.
- Value objects are immutable; entities have identity but mutation is confined to engine boundaries.
- Domain layer has no dependencies on infrastructure, plugins, or the CLI.
