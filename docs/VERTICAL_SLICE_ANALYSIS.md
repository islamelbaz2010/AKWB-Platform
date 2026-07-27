# AKWB Vertical Slice Analysis

**Goal:** Determine whether a user can install AKWB today and run `akwb analyze
myproject` successfully.  
**Answer:** No.  
**Status:** Sprint 7 blocker analysis.

## Test Scenario

```bash
pip install -e .
mkdir myproject
cd myproject
akwb init .
akwb analyze .
```

## Result of Each Step

| Step | Expected | Actual | Verdict |
|---|---|---|---|
| `pip install -e .` | Package installs and `akwb` CLI is available. | Unverified in environment; `pyproject.toml` defines the `akwb` console script. | Likely OK. |
| `akwb init .` | Creates `.akwb/workspace.json`. | Implemented. Works. | Pass. |
| `akwb analyze .` | Discovers files, extracts knowledge, builds graph, writes workspace. | **Command does not exist.** | **Fail.** |

## CLI Evidence

The `akwb` CLI in `src/akwb/cli.py` registers only four commands:

- `version`
- `init`
- `doctor`
- `discover`

There is no `analyze` command registered. `grep -r "analyze" src/akwb/*.py`
returns no matches.

## What Would Fail Even If `analyze` Existed

If a developer added a stub `analyze` command today, the following would still
fail because the components are not wired:

1. **No `ExtractionPipeline` in `Container`**. The pipeline is not instantiated
   or configured with plugins.
2. **No `GraphEngine` in `Container`**. The graph engine is not available to the
   CLI.
3. **No plugin loading in CLI flow**. `Container.load_plugins()` is never
   called, so any plugin reader or extractor would not be used.
4. **No file reading loop**. `DiscoveryEngine` produces an `ArtifactRegistry`, but
   no code iterates over it, reads bytes, and calls `ExtractionPipeline.extract()`.
5. **No `KnowledgeCatalog` assembly**. `ExtractionPipeline.extract()` returns a
   list of `KnowledgeObject`s. No code aggregates them into a `KnowledgeCatalog`
   with type definitions.
6. **No graph persistence**. `GraphEngine.save()` requires a `GraphStorage`
   backend. No backend is implemented. The workspace would not contain a graph.
7. **No report/export commands**. Even if the graph were built, there is no CLI
   to expose it.

## Blockers by Severity

| # | Blocker | Severity | Evidence |
|---|---|---|---|
| 1 | `akwb analyze` command missing | Critical | `src/akwb/cli.py` has no `analyze` command; `grep` confirms no occurrence. |
| 2 | `Container` does not wire `ExtractionPipeline` or `GraphEngine` | Critical | `src/akwb/container.py` only creates `DiscoveryEngine`. |
| 3 | No graph persistence backend | Critical | `GraphEngine.save()` raises `RuntimeError`; `GraphStorage` is only a port. |
| 4 | No `KnowledgeCatalog` assembly | High | `ExtractionPipeline.extract()` returns `ExtractionResult` with object list; no catalog aggregator exists. |
| 5 | No relationship extraction | High | `RelationshipBuilder` not found in source. Graph would be disconnected nodes. |
| 6 | CLI does not load plugins | Medium | `Container.load_plugins()` is defined but never called by CLI. |
| 7 | No `report` / `export` commands | Medium | `src/akwb/cli.py` lacks these commands. Downstream consumption blocked. |
| 8 | No source-code parser | Medium | `.py` files are read as text by `TextReader`; `RuleBasedExtractor` only matches keywords in text. |
| 9 | `UnitOfWork` not used | Low | Transaction staging exists but is not committed during any command. |

## Conclusion

AKWB cannot be used as a product today. The most critical gap is not a missing
feature; it is missing integration. The engine components exist as libraries but
are not connected to a CLI command. The second-most-critical gap is the lack of
graph persistence, which prevents any downstream product from consuming the
workspace. Sprint 7 must close these integration gaps before adding languages
or AI features.
