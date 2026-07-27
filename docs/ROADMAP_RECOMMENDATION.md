# AKWB Roadmap Recommendation

## Goal

Optimize the existing roadmap for:

- **Business value:** Deliver a reusable engine as soon as possible.
- **Reuse:** Avoid duplicating downstream product capabilities.
- **Maintainability:** Reduce unnecessary abstractions and scope creep.
- **Development speed:** Close the end-to-end gap before adding more features.

## Current Roadmap Snapshot

The existing `docs/20_ROADMAP.md` proposes:

- **Phase 1: Foundation (Sprints 1–3)** — CLI, config, domain model, storage,
  discovery, plugin loader.
- **Phase 2: Knowledge Extraction (Sprints 4–6)** — Parser/extractor API,
  Knowledge graph, incremental analysis.
- **Phase 3: AI Context & Reports (Sprints 7–9)** — AI Engine context builders,
  summarization, chunking, embeddings, reports.
- **Phase 4: Ecosystem & Hardening (Sprints 10–12)** — Plugin marketplace,
  security, packaging, performance, beta.
- **Phase 5: Scale & Enterprise (Future)** — Remote analysis, federation,
  dashboard, API, enterprise policy.

## Recommended Changes

1. **Remove the AI Engine sprint from core AKWB.** AI context generation,
   summarization, chunking, embeddings, and RAG are better owned by downstream
   products such as **AI Context Builder** and **Eunoia AI OS**. AKWB should
   export the raw `KnowledgeGraph`; downstream products transform it into
   context.
2. **Remove the Marketplace sprint from MVP.** A signed plugin marketplace is
   valuable but not required for the engine to be reusable. Defer until after
   public beta.
3. **Add an end-to-end integration sprint immediately.** The `akwb analyze`
   command and graph persistence are missing. This is the highest-value next
   step.
4. **Add a source-code parser sprint.** A Markdown parser alone cannot analyze
   software projects. Add a Python AST parser as the next concrete parser.
5. **Add a relationship extraction sprint.** Without edges, the Knowledge Graph
   is just a list of nodes. Import/call/reference resolution is required.
6. **Merge reports and exports.** Reports should be simple export artifacts
   (Markdown/JSON), not a product feature.

## Revised Roadmap

### Phase 1: Foundation (Complete)

| Sprint | Deliverable | Status |
|---|---|---|
| Sprint 1 | Core CLI (`version`, `init`, `doctor`), config, DI container, storage, events, observability, workspace bootstrap | Complete |
| Sprint 2 | Discovery engine: scanning, classification, fingerprinting, incremental diff, artifact registry | Complete |
| Sprint 3 | Knowledge Object Framework: models, types, relationships, evidence, validation, serialization | Complete |

### Phase 2: Extraction & Graph (Complete Libraries, Missing Integration)

| Sprint | Deliverable | Status |
|---|---|---|
| Sprint 4 | Extraction Pipeline: reader/segmenter/extractor/builder/validator plugin ports, rule-based extractor | Complete as library |
| Sprint 5 | Knowledge Graph Engine: graph model, index, query, traversal, validation, statistics | Complete as library |
| Sprint 6 | Markdown AST Parser: parser, AST, visitor, mapper, reader, segmenter | Complete and integrated |

### Phase 3: End-to-End Engine & Core Parsers (Next)

| Sprint | Theme | Goal | Deliverables |
|---|---|---|---|
| **Sprint 7** | End-to-End Analysis Command | Close the integration gap. | `akwb analyze <path>`, `Container` wires `DiscoveryEngine` -> `ExtractionPipeline` -> `GraphEngine`, persist workspace artifacts. |
| **Sprint 8** | Python Source Parser | Analyze real code, not just Markdown. | Python AST reader/segmenter/extractor; extract modules, classes, functions, methods, imports, docstrings. |
| **Sprint 9** | Relationship Extraction | Build a connected graph. | `RelationshipBuilder` port; import/call/inheritance/doc-to-code edges; dependency graph. |
| **Sprint 10** | Graph Persistence & Export API | Make the graph reusable. | `LocalGraphStorage` backend; write `graph_nodes.jsonl`, `graph_edges.jsonl`, `graph.dot`, `graph.cypher`; `akwb report` and `akwb export` commands. |

### Phase 4: Multi-Language & Ecosystem

| Sprint | Theme | Goal | Deliverables |
|---|---|---|---|
| **Sprint 11** | Node.js / JavaScript Parser | Expand language coverage. | JS/TS AST parser; extract components, functions, imports, package references. |
| **Sprint 12** | Plugin SDK & Reference Plugins | Enable third-party parsers. | `akwb plugin` CLI commands, plugin template, contract tests, documentation. |
| **Sprint 13** | Java / Go / Rust / PHP Parser Framework | Language-agnostic parser skeleton. | Generic parser adapter; one additional language parser (Java or Go). |

### Phase 5: Hardening & Beta Release

| Sprint | Theme | Goal | Deliverables |
|---|---|---|---|
| **Sprint 14** | Performance & Scalability | Meet 1M LOC / 5 min target. | Streaming readers/segmenters, batched extraction, memory-bounded graph, benchmarking harness. |
| **Sprint 15** | Security & Sandboxing | Make plugin loading safe. | Secret scanning, path sandboxing, plugin signature verification, threat model. |
| **Sprint 16** | Packaging & Distribution | Ship a beta. | PyPI package, signed releases, SBOM, CLI installers, documentation, migration guide. |

### Phase 6: Future (Post-Beta)

| Theme | Goal | Notes |
|---|---|---|
| **Plugin Marketplace** | Signed plugin distribution | Defer until plugin API is stable and there is demand. |
| **AI Context Bridge** | Optional downstream context export | Provide richer JSONL exports; let AI products do summarization/embeddings. |
| **Remote / Distributed Analysis** | Large monorepos / CI | Optional service mode; not core engine. |
| **Team Workspace Federation** | Aggregate multiple `.akwb/` workspaces | Enterprise feature; downstream concern. |
| **Web Dashboard / API** | Visualization and REST/gRPC | Owned by StayOS or a dedicated dashboard product. |

## Sprint Priority Rationale

1. **Sprint 7 first.** No end-to-end value exists until `akwb analyze` works.
   All prior sprints are libraries waiting to be orchestrated.
2. **Sprint 8 second.** AKWB must analyze code to be useful for software
   projects. Markdown-only is insufficient.
3. **Sprint 9 third.** A graph without edges is just a catalog. Relationships
   unlock downstream value.
4. **Sprint 10 fourth.** Persisting and exporting the graph is what makes
   AKWB reusable by other products.
5. **Sprints 11–13** expand language coverage and plugin ecosystem. These are
   growth sprints, not MVP blockers.
6. **Sprints 14–16** harden and release. Must happen after the engine is
   functional end-to-end.

## Sprints Removed or Deferred

| Original Sprint | Disposition | Reason |
|---|---|---|
| AI Engine context builders, summarization, chunking, embeddings | **Removed from core** | Owned by AI Context Builder / Eunoia AI OS. AKWB exports the graph; downstream products build context. |
| Report generation as product feature | **Merged into Export API** | AKWB produces raw Markdown/JSON/JSONL/DOT/Cypher. Downstream products render and publish. |
| Plugin marketplace | **Deferred post-beta** | Not required for engine reuse; adds security and distribution complexity. |
| Web dashboard | **Removed** | Out of engine scope. |
| Real-time watch mode | **Deferred** | Useful but not required for MVP. |
| Multi-project federation | **Deferred** | Enterprise/downstream feature. |
| Cloud/SaaS operations | **Removed** | Not an engine concern. |

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Sprint 7 integration is large and may delay value | Deliver `akwb analyze` in stages: first discovery + extraction, then graph build, then persistence. |
| Python parser is harder than Markdown | Start with `ast` module; defer type inference and dynamic analysis. |
| Relationship extraction is ambiguous | Use conservative, evidence-based edges with confidence scores; allow plugins to improve resolution. |
| Downstream products depend on AI features | Define a rich export format (JSONL nodes/edges + source spans + summaries) so AI products can consume it directly. |
| Plugin API churn | Stabilize core ports in Sprints 7–10 before inviting third-party plugins. |

## Conclusion

The revised roadmap focuses AKWB on becoming a working, reusable extraction and
graph engine before expanding into language coverage and ecosystem features. It
removes consumer-facing AI and marketplace work that duplicates downstream
products and delays the engine's core value.
