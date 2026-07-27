# Ready for Sprint 7

## Sprint 6 Completion Summary

The Enterprise Markdown AST Parser is complete and integrated with the
Extraction Pipeline.

- `MarkdownParser` produces a typed AST from Markdown files.
- `MarkdownReader` and `MarkdownSegmenter` are registered in the default
  extraction pipeline.
- All Markdown elements requested for this sprint are supported.
- Unit and integration tests cover parser behavior, AST traversal, file-based
  extraction, nested headings, tables, code, lists, mixed content, large files,
  and edge cases.
- Documentation and a runnable example are in place.

## Quality Gate Status

| Gate | Status |
|------|--------|
| `pytest` full suite | 192 passed, 0 failed |
| `ruff` linter | 0 issues |
| `mypy src/akwb/extraction` | 0 issues |
| Example script | Runs successfully |

## Components Ready for Sprint 7

- `MarkdownReader` plugin architecture
- `MarkdownSegmenter` rich segment production
- `MarkdownASTWalker` / `MarkdownASTVisitor` extension points
- `MarkdownASTMapper` normalization bridge
- Extraction Pipeline with Markdown support

## Recommended Sprint 7 Scope

Sprint 7 can focus on the next concrete parser(s) or an AI extraction bridge:

1. **Source Code AST Parser**
   - Parse Python (and optionally other languages) into an AST.
   - Extract components (modules, classes, functions), dependencies, and
     docstrings as `KnowledgeObject`s.
   - Register as a `Reader` plugin for source code artifacts.

2. **AI Extraction Bridge**
   - Add an `Extractor` plugin that sends `Segment`s to an LLM.
   - Convert LLM responses into `ExtractionCandidate`s.
   - Keep the pipeline AI-optional; the bridge is a plugin.

3. **Relationship Extraction**
   - Derive `KnowledgeRelationship`s between extracted objects (e.g., a
     decision references a component, a requirement depends on a decision).
   - Use source locations and heading hierarchy to infer parent/child and
     dependency links.

4. **Workspace Persistence Integration**
   - Write `KnowledgeCatalog` and graph artifacts to workspace storage through
     `StoragePort`.
   - Connect the extraction pipeline to the workspace lifecycle.

## Pre-Conditions

- The Extraction Pipeline now has a reference Markdown parser.
- New parsers can follow the same pattern: implement a `Reader`/`Segmenter` pair
  and register them in `ExtractionPipeline`.
- The Knowledge Framework and Graph Engine are ready to receive extracted
  `KnowledgeObject`s and relationships.

## Known Good Starting Points

- `src/akwb/extraction/markdown.py` for parser and AST patterns.
- `src/akwb/extraction/pipeline.py` for plugin registration.
- `src/akwb/extraction/plugins.py` for `Reader`, `Segmenter`, `Extractor`, and
  `CandidateBuilder` ports.
- `tests/integration/extraction/test_markdown_files.py` for integration test
  patterns with real files.
