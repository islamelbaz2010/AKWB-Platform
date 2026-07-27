# Data Model

## Purpose
Specify concrete schemas, serialization formats, and relationships for the entities, value objects, and artifacts produced by AKWB.

## Responsibilities
- Define JSON/JSONL schemas for persistence and exchange.
- Define identifier conventions, references, and foreign keys.
- Define property types and validation rules.
- Document backward-compatibility and schema-evolution rules.

## Core Entity Schemas

### Project
```json
{
  "id": "file:///path/to/project",
  "rootPath": "/path/to/project",
  "detectedProfiles": ["python", "fastapi"],
  "lastAnalysisAt": "2026-07-27T00:00:00Z",
  "snapshotId": "snap:sha256:..."
}
```

### SourceEntry
```json
{
  "relativePath": "src/app.py",
  "absolutePath": "/project/src/app.py",
  "fingerprint": {
    "algorithm": "sha256",
    "hash": "...",
    "size": 1234,
    "mtime": 1710000000
  },
  "language": "python",
  "role": "source",
  "mimeType": "text/x-python",
  "tags": ["entrypoint", "api"],
  "detectorId": "akwb.detector.python",
  "parserHint": "akwb.parser.python",
  "encoding": "utf-8"
}
```

### KnowledgeUnit
```json
{
  "id": "ku://project/src/app.py#UserService",
  "kind": "class",
  "name": "UserService",
  "qualifiedName": "src.app.UserService",
  "displayName": "UserService",
  "sourceRefs": [
    {
      "path": "src/app.py",
      "span": {"start": {"line": 10, "col": 0}, "end": {"line": 50, "col": 1}}
    }
  ],
  "properties": {
    "docstring": "...",
    "methods": ["get", "post"],
    "complexity": 5
  },
  "summary": "Handles user-related API operations.",
  "embeddingRef": "emb:..."
}
```

### Relationship
```json
{
  "id": "rel:...",
  "sourceId": "ku://...",
  "targetId": "ku://...",
  "kind": "imports",
  "confidence": 1.0,
  "evidence": {
    "path": "src/app.py",
    "span": {"start": {"line": 1, "col": 0}, "end": {"line": 1, "col": 20}}
  },
  "properties": {}
}
```

### Artifact
```json
{
  "id": "art:...",
  "kind": "report",
  "sourceRefs": ["ku://..."],
  "contentRef": ".akwb/reports/structure.md",
  "fingerprint": "...",
  "createdAt": "2026-07-27T00:00:00Z"
}
```

### ContextBundle
```json
{
  "id": "ctx:ask:impact",
  "task": "impact_analysis",
  "chunks": [
    {"unitId": "ku://...", "text": "...", "tokenCount": 120, "relevance": 0.95}
  ],
  "metadata": {"tokenBudget": 4000, "modelHint": "general"}
}
```

## Serialization Conventions
- JSONL for append-only, streaming collections (nodes, edges, facts, source entries).
- SQLite for queryable indexes and relational lookups.
- Parquet for large analytic datasets (optional).
- JSON for manifests and configuration.
- YAML for human-authored configuration.

## Identifier Conventions
- `ku://{projectId}/{relativePath}#{localId}` for knowledge units.
- `rel:{uuid}` for relationships.
- `art:{uuid}` for artifacts.
- `snap:{sha256}` for snapshots.

## Inputs
- Domain model.
- Workspace engine requirements.
- Storage model conventions.

## Outputs
- Schema definitions.
- Validation contracts.
- Persistence format specifications.

## Dependencies
- `04_DOMAIN_MODEL.md`
- `09_WORKSPACE_ENGINE.md`
- `15_STORAGE_MODEL.md`

## Future Extensions
- RDF/OWL export.
- Schema evolution with migrations.
- Typed property schemas per `KnowledgeUnit` kind.

## Risks
- Schema churn between versions; a migration strategy is required.
- Large JSONL files are hard to query; secondary indexes are essential.

## Design Decisions

- `ArtifactManifest` schema tracks every artifact id, kind, sourceRefs, contentRef, fingerprint, and createdAt in a single JSON document for crash recovery.
- `Package` and `Dependency` schemas capture dependency-manager data; `Dependency` is a relationship between packages or between a package and a knowledge unit.
- Repository interfaces (`ProjectRepository`, `SourceCatalogRepository`, `KnowledgeGraphRepository`, `ArtifactRepository`, `SnapshotRepository`, `ConfigRepository`) are defined as abstract ports.
- `EventEnvelope` wraps domain events with metadata (event id, timestamp, correlation id, version) for replay and observability.
- `KnowledgeUnit` and `Relationship` kind registries are versioned independently and documented as part of the workspace format.
- `workspace.json` carries a `schemaVersion` field; the storage layer runs migration hooks when opening an older workspace.
- JSONL is the primary persistence format for streaming and inspectability.
- Stable IDs derive from project-relative paths; renames are treated as new units until rename detection is implemented.
- Value objects are stored as embedded JSON; entities reference each other by ID.
- Schemas are versioned independently of AKWB release version.
