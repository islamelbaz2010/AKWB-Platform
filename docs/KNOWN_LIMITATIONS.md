# Known Limitations — Sprint 3 Enterprise Knowledge Object Framework

## Current Scope

This document records deliberate omissions and known limitations of the Enterprise Knowledge Object Framework after Sprint 3. These are not defects; they are items deferred to later sprints.

## 1. No Parsers or AI Extraction

The framework defines `KnowledgeSource`, `KnowledgeEvidence`, and `KnowledgeObject`, but it does **not** include any code that parses source files or extracts knowledge with AI. Those are separate engines that will *produce* `KnowledgeObject` instances.

## 2. Content Schema Validation Is Basic

`KnowledgeType.content_schema` supports:
- `required` field list
- `properties` with primitive JSON Schema `type` checks (`string`, `number`, `integer`, `boolean`, `array`, `object`, `null`)

It does **not** yet support:
- JSON Schema `oneOf`, `anyOf`, `allOf`, `$ref`, `enum`, `pattern`, `format`
- Nested object validation beyond one level of `properties`
- Array item schemas

## 3. No Query or Index Layer

`KnowledgeCatalog` stores objects and relationships in memory. There is no graph index, search index, or vector index yet. Sprint 4 is expected to add the Knowledge Graph & Indexing Engine.

## 4. No Persistence Beyond Serialization

Catalogs can be serialized to JSON/JSONL/YAML strings, but there is no persistent workspace storage integration (e.g., writing `.akwb/knowledge/catalog.jsonl` through `StoragePort`). That belongs to the Workspace / Publishing layer.

## 5. Relationship Rules Are Minimal

The `RelationshipValidator` checks:
- Relationship type is registered.
- Endpoints exist in the catalog (for `knowledge_object` references).
- Optional `allowed_from_types` / `allowed_to_types` constraints.

It does **not** enforce:
- Cyclic dependency detection globally.
- Cardinality rules (e.g., a decision may have at most one superseding decision).
- Domain-specific business semantics.

## 6. Lifecycle Workflow Is Not Automated

`KnowledgeLifecycle.transition` validates state changes, but there is no engine that automatically advances lifecycle based on external events (e.g., "publish when approved"). Automation will be added when a workflow/review layer is designed.

## 7. Confidence Is a Single Scalar

`KnowledgeConfidence.value` is a single float in `[0.0, 1.0]`. Multi-dimensional confidence (e.g., per-source, per-claim) and aggregation algorithms are not implemented.

## 8. Source Kinds Are a String Vocabulary

`KnowledgeSource.kind` is a plain string. The framework provides a `BUILTIN_SOURCE_KINDS` list for guidance, but there is no runtime registry enforcing valid source kinds. Evidence types are registry-based; source kinds could be registry-based in a future version.

## 9. No Streaming for JSONL

`JsonlSerializer` materializes the entire catalog as a single string. For very large catalogs, a streaming reader/writer should be added.

## 10. Version Merging Is Manual

The framework tracks `previous_version_id` and `superseded_by_id`, but it does not compute merged content or resolve conflicts between versions.

## Acceptance

These limitations are acceptable for the current sprint. They define the boundary between the data framework and the engines that will consume it.

---

# Known Limitations — Sprint 4 Enterprise Extraction Pipeline

## Current Scope

This document records deliberate omissions and known limitations of the Enterprise Extraction Pipeline after Sprint 4. These are not defects; they are items deferred to later sprints.

## 1. Built-in Extractor Is Rule-Based, Not Semantic

`RuleBasedExtractor` uses simple keyword heuristics and segment-type mappings. It does not use NLP, LLMs, code parsers, or AST analysis. The resulting candidates may miss context, nuance, or implicit relationships.

## 2. Reader Coverage Is Basic

The built-in readers handle plain text, binary blobs, and JSON/YAML. They do not parse DOCX, PDF, Markdown into rich ASTs, source code into ASTs, images via OCR, or audio/video into transcripts. Those are parser-specific sprints.

## 3. Segmentation Heuristics Are Line-Oriented

Heading, code, table, and paragraph detection uses regular expressions over raw text. It will not perfectly handle all Markdown dialects, nested structures, or non-Latin scripts. `AdaptiveSegmenter` dispatches by content kind but does not deeply analyze document structure.

## 4. No Relationship Extraction

The pipeline extracts isolated `KnowledgeObject`s. It does not derive `KnowledgeRelationship`s between objects, identify co-references, or link candidates to existing catalog objects.

## 5. Candidate Merging and Deduplication Are Not Implemented

Identical or near-duplicate candidates (e.g., a heading and the following paragraph that repeat the same idea) are emitted as separate objects. A candidate-resolution/deduplication stage should be added in a future sprint.

## 6. Confidence Is Defaulted

All built-in candidates receive `confidence=1.0` with `method="algorithm"`. Future extractors should estimate and propagate realistic confidence scores.

## 7. No Persistent Storage Integration

`ExtractionResult` is returned in memory. The pipeline does not write `KnowledgeCatalog` files to workspace storage or interact with `StoragePort`.

## 8. No Streaming

The entire artifact content is read and segmented in memory. Very large files may cause high memory usage. A streaming segmenter/reader should be added later.

## 9. Candidate Validation Is Static

`CandidateValidator`s check field presence and type registration. They do not cross-reference existing objects, enforce project-specific constraints, or perform semantic validation.

## 10. No AI Extraction Bridge

While the `Extractor` port is plugin-extensible, no AI/LLM-based extractor plugin is included in this sprint. Adding one is a clear next step.

## Acceptance

These limitations are acceptable for the current sprint. They define the boundary between the pipeline framework and the concrete parsers, AI extractors, and relationship engines that will consume it.

---

# Known Limitations — Sprint 5 Enterprise Knowledge Graph Engine

## Current Scope

This document records deliberate omissions and known limitations of the Enterprise Knowledge Graph Engine after Sprint 5.

## 1. In-Memory Only

The default `KnowledgeGraph` and `InMemoryGraphIndex` keep all nodes, edges, and indexes in memory. There is no built-in persistent graph storage implementation; only the abstract `GraphStorage` plugin port is provided.

## 2. No Graph Database Integration

As required, no Neo4j, TigerGraph, JanusGraph, or GraphDB integration is implemented. A future sprint may provide a `GraphStorage` plugin for an external store.

## 3. Query API Is Field-Based

`GraphQuery` supports conjunctions of simple field filters. It does not yet support pattern matching, nested graph traversals inside a query, Cypher/Gremlin-like query languages, or join/aggregation beyond counts.

## 4. Index Is Rebuilt on Graph Changes

`InMemoryGraphIndex` is built once per graph. Adding or removing nodes/edges after indexing requires rebuilding the index; there is no incremental update mechanism.

## 5. Cycle Detection Is Directed Only

`GraphValidator` detects directed cycles. It does not flag cycles that arise only from undirected `related_to` relationships, nor does it compute minimum feedback arc sets.

## 6. No Relationship Inference

The engine only materializes explicit `KnowledgeRelationship`s and object `references`. It does not infer implicit relationships (e.g., co-occurrence, shared source, semantic similarity).

## 7. No Graph Versioning or Time Travel

Graph snapshots are not versioned. Comparing graph states over time or rolling back to a previous graph state is not supported.

## 8. Statistics Are Basic

`GraphStatistics` computes counts, degrees, density, connected components, and SCC-based cycle counts. It does not compute centrality, PageRank, community structure, or clustering coefficients.

## 9. No Multi-Graph Support

A `KnowledgeGraph` is a single graph. There is no built-in support for multiple named graphs or graph overlays.

## 10. Storage Port Is Abstract

`GraphStorage` defines `save`/`load` signatures, but no concrete storage format (JSON, JSONL, binary, etc.) is implemented in this sprint.

## Acceptance

These limitations are acceptable for the current sprint. They define the boundary between the canonical graph abstraction and the concrete storage, parser, AI, and analytics engines that will consume it.

---

# Known Limitations — Sprint 6 Enterprise Markdown AST Parser

## Current Scope

This document records deliberate omissions and known limitations of the Enterprise Markdown AST Parser after Sprint 6.

## 1. Only Markdown Is Parsed

The parser handles Markdown and GFM extensions. It does not parse DOCX, PDF, source code ASTs, images via OCR, or audio/video transcripts.

## 2. Inline Formatting Is Flattened to Text

Bold, italic, strikethrough, and other inline formatting are preserved as text but not as separate AST nodes. Only links, images, inline code, and inline HTML are represented as distinct nodes.

## 3. Footnotes Are Collected in a Footnote Block

Footnote definitions are placed under a `footnote_block` container rather than as top-level document children. Consumers must traverse the block to locate individual `footnote` nodes.

## 4. Tables Are Converted to Row Lists

GFM tables are normalized to a list-of-lists representation. Column alignment and cell-level formatting are not retained as separate AST metadata.

## 5. HTML Blocks Are Preserved As-Is

Raw HTML blocks are kept as raw strings. They are not parsed into an HTML AST or DOM.

## 6. Source Locations Are Line-Based

Locations are recorded as `start_line` / `end_line` ranges. Column offsets and byte offsets are not tracked.

## 7. Task List Checked State Is Inferred from Source

The checked state of a task list item is determined by inspecting the original source line. If the Markdown token stream does not expose the checkbox state, the parser falls back to the source-line heuristic.

## 8. No Relationship Extraction

The parser extracts rich segments but does not derive `KnowledgeRelationship`s between headings, paragraphs, code blocks, tables, or list items. Relationship inference is a future pipeline stage.

## 9. Large Files Are Processed in Memory

The entire Markdown text and AST are held in memory. Streaming parsing for very large files is not implemented.

## 10. No Persistent Caching

Parsed ASTs and segments are not cached on disk. Repeated extraction of the same artifact re-parses from scratch.

## Acceptance

These limitations are acceptable for the current sprint. The parser provides the reference architecture for future concrete parsers while remaining focused on Markdown AST support.

