# Ready for Sprint 5

## Sprint 4 Completion Summary

The Enterprise Extraction Pipeline is implemented, tested, documented, and integrated with the existing plugin architecture and the Sprint 3 Knowledge Object Framework.

## Quality Gate

| Gate | Status |
|---|---|
| All tests pass | ✅ |
| Lint clean (ruff) | ✅ |
| Type check clean (mypy `src/akwb/extraction`) | ✅ |
| Documentation | ✅ |
| Usage example | ✅ |
| No forbidden code (parsers, AI, reports, publishing, workspace generation) | ✅ |

## What Is Ready

1. `ExtractionPipeline` can be instantiated and used to convert `Artifact` + raw content into `KnowledgeObject` instances.
2. Built-in readers support text, binary, and JSON/YAML structured content.
3. Built-in segmenters support headings, paragraphs, code blocks, tables, structural JSON/YAML nodes, sentence-level semantics, and adaptive composition.
4. Built-in `RuleBasedExtractor` converts segments into `ExtractionCandidate`s using keyword heuristics.
5. `DefaultKnowledgeObjectBuilder` converts validated candidates into canonical `KnowledgeObject`s with sources and evidence.
6. Candidate validators ensure required fields and registered knowledge types.
7. Final objects are validated through the Sprint 3 `KnowledgeFramework`.
8. The pipeline is plugin-extensible via `Reader`, `Segmenter`, `Extractor`, `CandidateBuilder`, and `CandidateValidator` ports.

## Recommended Sprint 5 Scope

Sprint 5 should be **Concrete Parsers** (the first set of format-specific parsers) or **AI Extraction Bridge** (pluggable LLM/AI extractor). Recommended order:

1. **Concrete Parsers** first, because the pipeline already has reader/segmenter/extractor ports but no real DOCX, PDF, Markdown, or code AST readers. Implementing one or two concrete parsers will validate the pipeline with real-world artifacts.
2. **AI Extraction Bridge** next, inserting an `Extractor` implementation that delegates to an LLM API and returns candidates. This keeps AI logic isolated from the pipeline core.

## Pre-Conditions for Sprint 5

- Extraction pipeline tests and documentation are merged.
- `NormalizedContent`, `Segment`, `ExtractionCandidate`, and `ExtractionResult` schemas are stable.
- Plugin ports are documented and a sample plugin fixture exists.

## Known Good Starting Points

- `src/akwb/extraction/pipeline.py` — `ExtractionPipeline`
- `src/akwb/extraction/plugins.py` — extension ports
- `src/akwb/extraction/readers.py` — built-in readers
- `src/akwb/extraction/segmenters.py` — segmentation engine
- `src/akwb/extraction/extractors.py` — `RuleBasedExtractor`
- `src/akwb/extraction/builders.py` — candidate builder and validators
- `tests/unit/extraction/test_integration.py` — plugin integration pattern

## Approval

This project is ready for Sprint 5 planning and implementation.
