# Knowledge Engine

## Purpose
Define how raw sources are parsed, analyzed, and transformed into a structured, queryable knowledge graph with traceability.

## Responsibilities
- Parse source files into language-agnostic structural representations.
- Extract entities such as modules, classes, functions, APIs, variables, concepts, and documents.
- Extract relationships such as imports, calls, inheritance, references, and dependencies.
- Build and maintain the `KnowledgeGraph`.
- Support incremental updates via fingerprint invalidation.
- Provide hooks for cross-language and cross-file `RelationshipBuilder` plugins.

## Inputs
- `SourceCatalog` from the Discovery Engine.
- Parser, extractor, and relationship-builder plugins.
- Configuration: extraction depth, enabled extractors, parse timeout, relationship confidence threshold.
- Prior `KnowledgeGraph`, fingerprints, and cache entries.

## Process
1. **Scheduling:** For each `SourceEntry`, select parser and extractor plugins using `parserHint` and `role`.
2. **Parsing:** The parser returns a normalized model (e.g., `CodeModel`, `DocumentModel`). Parsing is lazy; failures are recorded as diagnostics.
3. **Extraction:** Extractors traverse the parsed model to emit `KnowledgeUnit`s and `Relationship`s.
4. **Relationship Building:** Run `RelationshipBuilder` plugins to add cross-file edges (e.g., import resolution, test-to-code links, doc-to-code links).
5. **Graph Assembly:** Merge units and edges into `KnowledgeGraph`; deduplicate by stable id; assign confidence.
6. **Enrichment:** Add derived properties such as complexity, coupling, documentation coverage, and ownership.
7. **Traceability:** Link tests to code, documentation to code, and configuration to features where evidence exists.

## Outputs
- `KnowledgeGraph` aggregate.
- `KnowledgeUnit` and `Relationship` collections.
- `KnowledgeExtracted` and `RelationshipInferred` domain events.
- Extraction diagnostics (parse errors, unsupported files, timeout reports).

## Dependencies
- `04_DOMAIN_MODEL.md`
- `06_PLUGIN_ARCHITECTURE.md`
- `07_DISCOVERY_ENGINE.md`
- `14_INCREMENTAL_ANALYSIS.md`

## Future Extensions
- Fusion of static and dynamic analysis traces.
- Code execution trace ingestion.
- Natural-language requirement extraction from docs and issues.
- Semantic diff and rename detection.

## Risks
- Parser plugins may fail on malformed or cutting-edge syntax.
- Cross-file relationship resolution can be ambiguous.
- Incremental graph updates may miss transitive relationship changes.

## Design Decisions

- An `IdentityResolver` merges duplicate `KnowledgeUnit`s emitted by overlapping extractors using stable IDs, qualified names, and source spans.
- A `TraceabilityBuilder` port links tests to code, docs to code, and configuration to features after the initial extraction phase.
- Cross-language relationships are resolved through shared identifiers such as file paths, import maps, and package names.
- Dependency extraction produces `Package` and `Dependency` entities from manifest files in addition to source-derived knowledge units.
- Graph algorithms (connected components, cycles, impact propagation) are implemented in `knowledge` or a future `graph` module using the persisted graph index.
- Parse failures are captured as `Diagnostic` value objects; the engine continues and reports diagnostics in the workspace.
- Knowledge units are identified by stable project-relative URIs.
- Parsing errors do not fail analysis; diagnostics are recorded and surfaced.
- Relationship inference uses confidence scoring; weak edges are kept but flagged.
- The graph is built in memory during analysis and persisted by the Workspace Engine.
- Extraction depth is configurable: `minimal` (summary only), `standard`, `deep` (full semantic graph).
