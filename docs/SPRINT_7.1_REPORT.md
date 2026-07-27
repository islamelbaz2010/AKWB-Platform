# Sprint 7.1 — Knowledge Fidelity Foundation Report

## Executive Summary

Sprint 7.1 hardened the architectural foundation of the AKWB platform without changing the product vision or user-facing behavior. The sprint delivered:

- A **Canonical Document Model** that normalizes document content into a parser-agnostic AST, enabling future DOCX/PDF/HTML parsers to plug into the same extraction pipeline as Markdown.
- A **production-grade Ignore Policy** with layered rules, directory/anchored/negation patterns, archive handling, and safe binary detection, surfaced through a backwards-compatible `IgnoreEngine` facade.
- **Workspace output deduplication** so `graph/` holds the combined/visual/query graph artifacts and `knowledge/` holds the node/edge JSONL files, matching the documented workspace layout.
- **Pipeline contract improvements**, including `ExtractionPipeline.can_extract(...)` and a `warning`-level skip path in `AnalyzeEngine` for unsupported MIME types, preventing real-world repositories from producing a false-positive analysis failure.

No new product features or AI/LLM components were introduced.

## Architecture

### Canonical Document Model

`src/akwb/extraction/document.py` defines the new canonical abstraction:

- `CanonicalElementType` — an enumeration of structural element kinds (`HEADING`, `PARAGRAPH`, `CODE`, `TABLE`, `TASK_LIST`, etc.).
- `DocumentElement` — a recursive Pydantic model carrying `id`, `type`, `level`, `content`, `location`, `metadata`, and `children`.
- `CanonicalDocument` — a typed root document with `source_uri`, `mime_type`, `language`, `metadata`, and a list of `DocumentElement`s.
- `DocumentReader` — an abstract `Reader` subclass whose `read_canonical` implementation is wrapped into the standard `Reader.read` interface, returning `NormalizedContent(kind=ContentKind.DOCUMENT)`.
- `CanonicalSegmenter` — a `Segmenter` that turns a `CanonicalDocument` tree into `Segment` objects for downstream extraction.
- `MarkdownCanonicalMapper` — maps the existing Markdown AST (`MarkdownDocument`/`MarkdownNode`) into the canonical model.

The extraction pipeline now registers `CanonicalSegmenter` in `AdaptiveSegmenter` and exposes the new types through `akwb/extraction/__init__.py`.

### Ignore Policy

`src/akwb/discovery/ignore_policy.py` introduces `IgnorePolicy` and supporting value objects (`IgnoreReason`, `IgnoreRule`, `IgnoreCheck`). The policy layers rules in priority order:

1. User explicit overrides (`!pattern`).
2. User ignore patterns from `.akwbignore` and `DiscoveryConfig`.
3. Repository `.gitignore`.
4. Built-in defaults covering OS artifacts, editor metadata, caches, generated folders, archives, and `.akwb/` itself.

It supports directory-only (`dir/`), anchored (`/path/to/file`), and negation (`!pattern`) syntax via `fnmatch`, plus safe binary detection through content sampling. The legacy `IgnoreEngine` (`src/akwb/discovery/ignore.py`) was refactored to delegate to `IgnorePolicy`, preserving the public API.

### Workspace Output Deduplication

`src/akwb/graph/storage.py` `LocalGraphStorage.save` is now target-specific:

- `graph/` writes `graph.jsonl`, `graph.dot`, and `graph.cypher`.
- `knowledge/` writes `graph_nodes.jsonl` and `graph_edges.jsonl`.
- Other directories continue to write all five files for backwards compatibility.

The `AnalyzeEngine` manifest was updated so `graph_nodes.jsonl` and `graph_edges.jsonl` point at `knowledge/`.

## Changes

| Area | Files | Change |
|------|-------|--------|
| Canonical Document Model | `src/akwb/extraction/document.py` (new), `src/akwb/extraction/models.py`, `src/akwb/extraction/segmenters.py`, `src/akwb/extraction/pipeline.py`, `src/akwb/extraction/__init__.py` | Parser-agnostic document AST, `DOCUMENT` `ContentKind`/`SegmentType`, `CanonicalSegmenter` wired into `AdaptiveSegmenter`, public exports. |
| Ignore Policy | `src/akwb/discovery/ignore_policy.py` (new), `src/akwb/discovery/ignore.py`, `src/akwb/discovery/engine.py`, `src/akwb/discovery/scanner.py` | Layered ignore rules, built-in/user/`.gitignore` support, binary/archive detection, directory/anchored/negation patterns, legacy `IgnoreEngine` facade preserved. |
| Workspace Deduplication | `src/akwb/graph/storage.py`, `src/akwb/analysis/engine.py` | Target-specific graph saves; `knowledge/` gets nodes/edges, `graph/` gets combined/dot/cypher. |
| Pipeline Contracts | `src/akwb/extraction/pipeline.py`, `src/akwb/analysis/engine.py` | Added `ExtractionPipeline.can_extract`; analysis skips unsupported MIME types as warnings instead of failing. |
| Documentation | `README.md`, `docs/07_DISCOVERY_ENGINE.md`, `docs/09_WORKSPACE_ENGINE.md`, `docs/EXTRACTION_PIPELINE.md` | Updated workspace tree, discovery design decisions, extraction pipeline domain model and module list. |

## Backwards Compatibility

- All existing public APIs remain intact.
- `IgnoreEngine` continues to expose its original interface; internal behavior is delegated to `IgnorePolicy`.
- `ExtractionPipeline.extract` still returns `ok=False` for an unregistered MIME type in a direct call; `AnalyzeEngine` now pre-checks and converts such cases into warnings to keep the end-to-end `akwb analyze` command healthy.
- Graph storage default behavior for unknown target directories is unchanged (all five files).
- Workspace `graph/` and `knowledge/` contents are reorganized to match the documented layout; `graph.cypher` is now consistently produced in `graph/`.

## Validation

- `python3 -m pytest -q` — **all tests pass**.
- `python3 -m ruff check src tests` — **no lint errors**.
- `python3 -m mypy src` — **26 pre-existing errors** related to PEP 695 generic syntax (`class Result[T, E]:`, `class TypeRegistry[T]:`) and the installed `mypy` version not yet supporting that syntax. No new type errors were introduced by the sprint changes.
- Sample project (`/Users/ahmed/Documents/Projects/demo-test`):
  - `akwb analyze ... --json` returned `ok: true`.
  - `akwb export jsonl`, `akwb export cypher`, and `akwb export dot` all produced valid output.
  - Workspace populated `index/source_catalog.jsonl`, `knowledge/catalog.jsonl`, `knowledge/graph_nodes.jsonl`, `knowledge/graph_edges.jsonl`, `graph/graph.jsonl`, `graph/graph.dot`, and `graph/graph.cypher`.

## Known Debt

- `mypy` cannot type-check the PEP 695 generic classes (`Result`, `TypeRegistry`) until the tooling catches up; consider reverting to explicit `Generic[T]`/`Generic[T, E]` bases if strict type checking is required before mypy support lands.
- The canonical document model is wired but not yet used by the default Markdown flow; the existing Markdown AST path remains primary. Migrating Markdown to `DocumentReader` is a future, low-risk refactor.
- `knowledge/graph_index.sqlite` is part of the documented workspace layout but is not currently produced.

## Recommendations

1. **Adopt the canonical model for the next parser** (HTML, DOCX, PDF) to prove the abstraction in a real plugin.
2. **Add dedicated readers** for common textual MIME types (`application/javascript`, `application/x-sh`, `application/x-sql`) so they are treated as `text/*` rather than skipped, improving knowledge coverage without breaking existing behavior.
3. **Resolve the PEP 695 typing debt** by either upgrading mypy when support is available or explicitly inheriting from `Generic`.
4. **Continue extending `IgnorePolicy` diagnostics** (`IgnoreCheck`) so `akwb doctor` can report which patterns ignored which paths.
5. **Consider a workspace migration tool** if downstream consumers rely on the previous duplicate `knowledge/graph.*` files; the current contract (`DOWNSTREAM_CONTRACT.md`) already specifies the correct layout, so this is low risk.
