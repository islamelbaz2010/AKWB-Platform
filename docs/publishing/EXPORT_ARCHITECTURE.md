# Export Architecture

## Purpose

Define how generated knowledge documents are converted into concrete artifacts in concrete locations and formats. Exporters are **adapters**, not core logic. The core `PublishingEngine` decides *what* to export; exporters decide *how* and *where*.

## Responsibilities

- Provide an `ExportPort` that all exporters implement.
- Decouple output format and output destination from document planning and generation.
- Support the required export targets: `workspace`, `ai-context`, `memory`, `reports`, `documentation`, `indexes`, `prompt-packs`, `review-packages`, `executive-packages`.
- Preserve traceability and source references in every exported artifact.
- Enable incremental export: only changed or invalidated documents are re-exported.
- Avoid hardcoded folder names in core; exporters receive target specs from configuration or CLI.

## Principles

- **Exporters are plugins.** No built-in Markdown, HTML, DOCX, PDF, JSON, or workspace serialization logic lives in the core.
- **Output-format agnostic.** The core `GeneratedDocument` abstraction does not know its final serialization.
- **No hardcoded folders.** Core passes a `target` URI/path to the exporter; default targets may be configured but are not fixed in code.
- **Traceability preserved.** Exporters must embed or sidecar source references; they must not strip provenance.
- **Incremental.** Exporters compare export fingerprints and skip unchanged outputs.

## Core Concepts

### `ExportPackage`

A collection of documents plus metadata ready for serialization.

| Field | Meaning |
|---|---|
| `package_id` | UUID. |
| `target` | `ExportTarget` specifying destination and options. |
| `documents` | `GeneratedDocument[]` to export. |
| `manifest` | Draft `PublishingManifest` containing plan and lineage. |
| `format_options` | Exporter-specific options (e.g., `template_id`, `toc`, `locale`). |

### `ExportTarget`

| Field | Meaning |
|---|---|
| `target_type` | `local_path`, `workspace`, `s3`, `api`, `stdout`. |
| `uri` | Destination URI or path (optional for `stdout`). |
| `format` | Requested MIME type or format hint (`markdown`, `json`, `html`, `docx`, `pdf`, `akwb-context`, `prompt-pack`). |
| `options` | Exporter-specific map. |

### `ExportResult`

| Field | Meaning |
|---|---|
| `exporter_id` | Plugin identifier. |
| `target` | Original target. |
| `exported_paths` | List of paths/URIs written. |
| `fingerprints` | Content fingerprints for incremental diff. |
| `diagnostics` | Warnings/errors. |

### `ExportTargetSpec`

A capability declaration used by `ExporterRegistry` to match exporters to targets.

| Field | Meaning |
|---|---|
| `target_type` | `local_path`, `workspace`, `s3`, `api`, `stdout`. |
| `formats` | List of supported format strings (e.g., `markdown`, `json`, `docx`). |
| `default_options` | Default options for this exporter. |

### `ExporterRegistry`

- Populated from plugin manifest `ports` entries.
- Selects the best exporter for a target by `format` and `target_type`.
- Falls back to a user-configured default exporter.
- Exporters declare capabilities through `supported_targets` returning `ExportTargetSpec[]`.

## Exporter Plugin Port

```python
class Exporter(ABC):
    port_name: str = "exporter"

    @property
    @abstractmethod
    def supported_targets(self) -> list[ExportTargetSpec]:
        """Return target types and formats this exporter supports."""
        ...

    @abstractmethod
    def can_export(self, package: ExportPackage) -> bool:
        """Return True if this exporter can handle the package target."""
        ...

    @abstractmethod
    def export(self, package: ExportPackage) -> ExportResult:
        """Serialize the package and return results."""
        ...
```

## Exporter Categories

These are conceptual categories, not core classes. A single plugin may implement one or more exporter behaviors.

| Category | Typical Target | Description |
|---|---|---|
| **Workspace Exporter** | `.akwb/` | Writes generated artifacts and the `PublishingManifest` into the project workspace. |
| **AI Context Exporter** | `.akwb/context/` or external RAG target | Produces token-aware context bundles, chunks, and optional vector indexes. |
| **Memory Exporter** | `.akwb/memory/` or external memory store | Writes durable facts, summaries, and entity indexes. |
| **Reports Exporter** | `.akwb/reports/` or external report target | Produces human-readable reports (Markdown/HTML). |
| **Documentation Exporter** | `docs/` or external wiki | Produces project documentation sites or pages. |
| **Indexes Exporter** | `.akwb/index/` or external search index | Builds keyword, graph, or vector indexes. |
| **Prompt Packs Exporter** | `.akwb/prompts/` or external prompt registry | Writes reusable prompt sets. |
| **Review Packages Exporter** | `.akwb/reviews/` or external review system | Produces packages for manual review with context. |
| **Executive Packages Exporter** | `.akwb/executive/` or external dashboard | Produces high-level summaries for non-technical stakeholders. |

> **Important:** None of the folder names above are hardcoded in core. They are default values that exporters may use when no explicit target is configured.

## Export Process

1. The `ExportEngine` receives `GeneratedDocument[]` and a draft `PublishingManifest`.
2. It groups documents by `ExportTarget`.
3. For each group, it asks `ExporterRegistry` to select an `Exporter`.
4. It builds an `ExportPackage` and calls `exporter.export(package)`.
5. The exporter serializes the package to the target location/format.
   - For `target_type=workspace`, the exporter writes through the `StoragePort` and is sandboxed inside `.akwb/`.
   - For other target types (`local_path`, `s3`, `api`, `stdout`), the exporter is responsible for I/O and must validate permissions itself; core does not perform the write.
6. The `ExportEngine` updates the `PublishingManifest` with `ExportRecord`s.
7. `DocumentExported` events are emitted.

## Incremental Export

- The `PublishingManifest` records the last `ExportResult` fingerprints per document and target.
- Before re-exporting, the `ExportEngine` compares the current `GeneratedDocument` fingerprint with the prior `ExportResult` fingerprint.
- If unchanged, the exporter may be skipped.
- If the exporter plugin version changed, all its prior outputs are invalidated.

## Target Resolution

The final target for an export is determined in this order (highest precedence first):

1. CLI flag (`--output-target <format>:<uri>`).
2. Per-document `PlannedDocument` export hint.
3. Project configuration `publishing.exports.<kind>.target`.
4. Global configuration `publishing.default_export_target`.
5. Exporter plugin default.

For `workspace` targets, `uri` is relative to `.akwb/`. For `local_path` targets, `uri` is a filesystem path relative to the project root or an absolute path.

## Inputs

- `GeneratedDocument[]` from Document Generation stage.
- Draft `PublishingManifest`.
- Effective configuration and CLI flags.
- `Exporter` plugins.

## Outputs

- Exported artifacts on disk, in workspace, or at remote targets.
- Updated `PublishingManifest` with `ExportRecord`s.
- `DocumentExported` events.
- Diagnostics.

## Dependencies

- `PUBLISHING_ARCHITECTURE.md`
- `PUBLISHING_PIPELINE.md`
- `DOCUMENT_PLANNING_ENGINE.md`
- `TRACEABILITY_MODEL.md`

## Future Extensions

- Multi-target export (one document to Markdown + PDF + JSON).
- Streaming export for large documents.
- Remote export to CMS, wiki, vector database, or CI artifact store.
- Export templates and theming as exporter options, not core concepts.

## Risks

- Exporters may disagree on target paths; `ExporterRegistry` must resolve deterministically.
- Large vector or binary exports may exceed disk budgets.
- Remote export failures need retry and diagnostic handling.
- Exporters may accidentally strip provenance if not validated.

## Design Decisions

- **Core never writes files.** The `ExportEngine` calls exporter plugins; exporters perform serialization. For `workspace` targets, exporters use the `StoragePort`; for other targets they use their own I/O with plugin-enforced permissions.
- **Exporter selection is by capability match, not hardcoded dispatch.** A target URI + format is matched to plugin `supported_targets` (`ExportTargetSpec`).
- **Traceability is a required exporter concern.** The `ExportResult` must include a statement that source references were preserved.
- **Export is idempotent.** Running the same export twice with unchanged inputs produces the same artifacts.
