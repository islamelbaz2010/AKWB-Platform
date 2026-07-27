# Workspace Engine

## Purpose
Define how AKWB materializes analyzed knowledge into a project-owned workspace containing artifacts, indexes, reports, graph exports, and AI context.

## Responsibilities
- Manage the `.akwb/` workspace directory.
- Persist `SourceCatalog`, `KnowledgeGraph`, artifacts, and indexes.
- Generate human-readable and structured reports.
- Export the knowledge graph in standard formats.
- Write project memory and context artifacts.
- Maintain `workspace.json` manifest and artifact index.
- Clean up stale or obsolete artifacts during incremental updates.

## Inputs
- `SourceCatalog` from the Discovery Engine.
- `KnowledgeGraph` from the Knowledge Engine.
- AI context bundles from the AI Engine.
- Configuration: output formats, enabled reports, retention policies.
- Prior workspace state and artifact manifest.

## Process
1. **Workspace Layout Check:** Ensure `.akwb/` exists; read or create `workspace.json`.
2. **Artifact Planning:** Based on configuration, plan artifacts to generate (index, graph, reports, memory, context).
3. **Serialization:** Write `SourceCatalog` and `KnowledgeGraph` to storage (JSONL, SQLite, optional Parquet).
4. **Report Generation:** Invoke `Reporter` plugins to produce Markdown/HTML/JSON reports.
5. **Graph Export:** Export nodes and edges to JSONL, DOT, and Cypher as configured.
6. **Context Packaging:** Package AI context bundles into `context/` directory.
7. **Memory Dump:** Write project memory as structured facts and summaries.
8. **Manifest Update:** Update the artifact manifest with fingerprints and references.
9. **Cleanup:** Remove artifacts whose source inputs have been deleted or invalidated.

## Workspace Layout
```
.akwb/
  workspace.json          # manifest, version, project id
  config/                 # effective configuration snapshot
  index/
    source_catalog.jsonl
    file_fingerprints.json
  knowledge/
    graph_nodes.jsonl
    graph_edges.jsonl
    graph_index.sqlite
  memory/
    facts.jsonl
    summaries.json
  context/
    context_bundle.json
    chunks/
    vector.index
  reports/
    structure.md
    coverage.md
    knowledge_graph.md
  graph/
    graph.jsonl
    graph.dot
  cache/
    parsed/
    extracted/
  logs/
    analysis.log
    audit.log
```

## Outputs
- `.akwb/` workspace artifacts.
- `workspace.json` manifest.
- `ArtifactProduced` and `WorkspaceSealed` events.
- Console report paths and summaries.

## Dependencies
- `04_DOMAIN_MODEL.md`
- `08_KNOWLEDGE_ENGINE.md`
- `10_AI_ENGINE.md`
- `11_DATA_MODEL.md`
- `15_STORAGE_MODEL.md`

## Future Extensions
- Custom workspace templates.
- Remote artifact publishing.
- Workspace visualizer (web UI).
- Team-level workspace aggregation.

## Risks
- Workspace corruption due to partial writes; atomic writes and manifest versioning mitigate this.
- Stale artifacts not cleaned up; the artifact manifest must track lineage.
- Users may commit `.akwb/` and bloat repositories; documentation must recommend `.gitignore` settings.

## Design Decisions

- `ArtifactManifest` is the source of truth for all generated artifacts and their lineage; it is updated atomically with `workspace.json`.
- Workspace writes use a two-phase commit: new artifacts are written to a staging area and promoted only after all engines succeed.
- Workspace recovery reads the last valid `workspace.json` and rolls back incomplete writes on startup.
- Report generation uses pluggable templates (Jinja/Mustache) rendered from persisted artifacts, not from live engine state.
- Workspace schema version is written into `workspace.json`; the engine can invoke migration hooks for major format changes.
- `akwb clean` preserves configuration and the latest snapshot manifest while removing cache and derived artifacts.
- Workspace is a directory inside the project; the platform never holds it.
- Artifact manifests are versioned for crash safety.
- Atomic file writes via temporary file + rename.
- Reports are generated from persisted artifacts, not directly from live engine state.
