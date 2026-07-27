# Sprint 7.2 — Canonical Architecture Validation Report

## 1. Executive Summary

Sprint 7.2 made the Canonical Document Model the single, official extraction path for all document content. Markdown no longer enters the old Markdown-specific segmentation path; it now produces a `CanonicalDocument` and is validated, segmented, and extracted by generic canonical components. A `CanonicalValidator` enforces the document contract before extraction, and a minimal `StubDocumentReader` proves that future parsers can be plugged in by implementing `DocumentReader` alone.

No new product features, AI/LLM components, or CLI commands were added.

## 2. Architecture Audit

### Legacy Paths Identified

- `MarkdownReader` (`src/akwb/extraction/markdown.py`) returned `NormalizedContent(kind=MARKDOWN, content=MarkdownDocument)`.
- `MarkdownSegmenter` consumed `MarkdownDocument` directly, bypassing the Canonical model.
- `AdaptiveSegmenter` declared `ContentKind.MARKDOWN` support.
- `ExtractionPipeline` registered both `CanonicalSegmenter` and `MarkdownSegmenter`.
- The `DocumentReader` contract existed but was not used by the default Markdown reader.

### Migration Applied

| Legacy Path | Change |
|-------------|--------|
| `MarkdownReader` | Now inherits `DocumentReader` and emits `CanonicalDocument` via `MarkdownCanonicalMapper`. |
| `MarkdownSegmenter` | No longer registered in the default pipeline. It remains in the module for backwards compatibility but is not part of the active architecture. |
| `AdaptiveSegmenter` | Removed `ContentKind.MARKDOWN` from supported kinds. |
| `ExtractionPipeline` | Registers only `CanonicalSegmenter` for document content; validates every `CanonicalDocument` with `CanonicalValidator` before segmentation. |
| `CanonicalValidator` | New validation layer between the Reader and segmentation. |

## 3. Migration Summary

### Source Files Changed

- `src/akwb/extraction/document.py`
  - Added `CanonicalValidationResult` and `CanonicalValidator`.
  - Added `TABLE_HEAD` and `TABLE_BODY` element types.
- `src/akwb/extraction/markdown.py`
  - `MarkdownReader` now subclasses `DocumentReader` and implements `read_canonical`.
  - Removed direct `ExtractionContext` import; uses `getattr(context, "project_id", None)`.
- `src/akwb/extraction/pipeline.py`
  - Imports and instantiates `CanonicalValidator`.
  - Removes `MarkdownSegmenter` from the adaptive segmenter list.
  - Validates `CanonicalDocument` immediately after reading.
- `src/akwb/extraction/segmenters.py`
  - `AdaptiveSegmenter.supported_content_kinds` no longer lists `MARKDOWN`.
- `src/akwb/extraction/__init__.py`
  - Exports `CanonicalValidator` and `CanonicalValidationResult`.
- `src/akwb/analysis/engine.py` (from Sprint 7.1)
  - Skips unsupported MIME types with warnings rather than failing analysis.

### Test Files Changed

- `tests/unit/extraction/test_markdown.py`
  - Updated reader test to assert `ContentKind.DOCUMENT` and `isinstance(..., CanonicalDocument)`.
- `tests/unit/extraction/test_canonical_pipeline.py` (new)
  - `StubDocumentReader` proves the generic `DocumentReader` → `CanonicalDocument` → extraction path.
  - Tests validate that the pipeline accepts a generic reader and that `CanonicalValidator` rejects malformed hierarchy.

## 4. Validation Layer Design

`CanonicalValidator` (`src/akwb/extraction/document.py`) runs between Reader and Segmentation.

Responsibilities:

- **Structure:** The root must be a `CanonicalDocument` with `type == "document"`.
- **Required metadata:** `source_uri` is required; `mime_type` is recommended.
- **Element hierarchy:** Each parent type declares which child types are allowed. For example, `list` may only contain `list_item`, `task_list_item`, `container`, or `other`.
- **IDs:** Every `DocumentElement` must have a non-empty, document-unique `id`.
- **References:** Placeholder validation for link/reference metadata and location shape.
- **Unsupported structures:** Unknown element types generate warnings; malformed structures generate errors and stop extraction.

Usage in `ExtractionPipeline.extract`:

```python
if normalized.kind == ContentKind.DOCUMENT:
    canonical_validation = self.canonical_validator.validate(
        normalized.content,
        source_ref=artifact.relative_path,
    )
    for diag in canonical_validation.diagnostics:
        context.emit(diag)
    if not canonical_validation.ok:
        return ExtractionResult(ok=False, ...)
```

## 5. Files Changed

- `src/akwb/extraction/document.py`
- `src/akwb/extraction/markdown.py`
- `src/akwb/extraction/pipeline.py`
- `src/akwb/extraction/segmenters.py`
- `src/akwb/extraction/__init__.py`
- `src/akwb/analysis/engine.py`
- `tests/unit/extraction/test_markdown.py`
- `tests/unit/extraction/test_canonical_pipeline.py`
- `docs/06_PLUGIN_ARCHITECTURE.md`
- `docs/EXTRACTION_PIPELINE.md`
- `docs/07_DISCOVERY_ENGINE.md`
- `docs/09_WORKSPACE_ENGINE.md`
- `README.md`

## 6. Compatibility Assessment

- All public classes (`MarkdownReader`, `MarkdownParser`, `MarkdownDocument`, `MarkdownSegmenter`, etc.) remain importable.
- `MarkdownReader` still satisfies the `Reader` public interface (`read(...)`) because `DocumentReader.read` is the standard wrapper.
- `MarkdownSegmenter` is no longer invoked by the default pipeline, but the class still exists and can be used manually or by explicit plugin registration.
- `ContentKind.MARKDOWN` remains in the enum for compatibility but is no longer emitted by built-in readers or consumed by the default segmenter.
- `akwb analyze` behavior from the user's perspective is unchanged: Markdown files are still analyzed and produce knowledge objects, reports, and graph artifacts.

## 7. Test Results

- `python3 -m pytest -q` — **pass** (all tests).
- `python3 -m ruff check src tests` — **pass** (no lint errors).
- `python3 -m mypy src` — **26 pre-existing errors**, all caused by the installed mypy version not supporting PEP 695 generics (`class Result[T, E]:` and `class TypeRegistry[T]:`). Two mypy variable-shadowing errors introduced by the Sprint were fixed before the final report.
- `akwb analyze /Users/ahmed/Documents/Projects/demo-test --json` — returned `ok: true` with 19,773 objects and 19,638 relationships.
- `akwb export jsonl|cypher|dot` on the sample workspace produced valid output.
- Workspace artifacts were generated in the canonical layout:
  - `.akwb/index/source_catalog.jsonl`
  - `.akwb/knowledge/catalog.jsonl`
  - `.akwb/knowledge/graph_nodes.jsonl`
  - `.akwb/knowledge/graph_edges.jsonl`
  - `.akwb/graph/graph.jsonl`
  - `.akwb/graph/graph.dot`
  - `.akwb/graph/graph.cypher`
  - `.akwb/reports/summary.json`
  - `.akwb/reports/summary.md`
  - `.akwb/workspace.json`

## 8. Remaining Technical Debt

- **PEP 695 typing debt:** `Result[T, E]` and `TypeRegistry[T]` use Python 3.12+ generic syntax that the current mypy cannot check. This is pre-existing and unrelated to the Canonical architecture.
- **Legacy `MarkdownSegmenter`:** Kept for backward compatibility but no longer part of the active pipeline. It could be deprecated in a future release.
- **Canonical element vocabulary:** The validator currently allows `OTHER` as a fallback child type. As more document parsers are added, the hierarchy map should be tightened if stricter validation becomes useful.
- **Reference validation:** `CanonicalValidator` validates structural references (link metadata) lightly; richer validation can be added as document parsers introduce more reference types.

## 9. Readiness Assessment

### Architecture Exit Criteria

| # | Question | Answer | Verification |
|---|----------|--------|--------------|
| 1 | Is there exactly one official document architecture? | **YES** | `DocumentReader` → `CanonicalDocument` → `CanonicalValidator` → `CanonicalSegmenter` is the only active path. |
| 2 | Can any future parser plug into the system without modifying Extraction? | **YES** | A parser only needs to subclass `DocumentReader` and emit a valid `CanonicalDocument`; `ExtractionPipeline` handles validation, segmentation, extraction, and knowledge-object building. This is proven by `tests/unit/extraction/test_canonical_pipeline.py::StubDocumentReader`. |
| 3 | Does every document now pass through the Canonical Model? | **YES** | Markdown produces a `CanonicalDocument` (`ContentKind.DOCUMENT`); `CanonicalSegmenter` is the only document segmenter registered in the pipeline. |
| 4 | Is the Validation Layer enforced? | **YES** | `ExtractionPipeline` calls `CanonicalValidator.validate` for every `DOCUMENT` kind before segmentation and returns a failed `ExtractionResult` if validation errors exist. |
| 5 | Is the architecture ready for Enterprise Document Readers? | **YES** | The contract is parser-agnostic, validated, and documented. DOCX, PDF, HTML, and email readers can be added by implementing `DocumentReader` without touching segmentation or extraction logic. |

## 10. Recommendation for Sprint 8

Implement the first Enterprise Document Reader (e.g., a plain-text or HTML reader) that exercises the `DocumentReader` → `CanonicalDocument` path end-to-end. This will validate that the Canonical model is sufficient for real non-Markdown document formats and surface any gaps in the element vocabulary or validation rules before adding more complex formats such as DOCX or PDF.
