# Performance Strategy

> **1.0.0 MVP implementation note:** This document describes the long-term performance target architecture. In AKWB 1.0.0 MVP the analysis pipeline is single-threaded, loads full file contents and graph/catalog buffers into memory, and does not include streaming, process/thread pools, content-addressable caches, SQLite graph spill, vector indexes, or profiling metrics. All such optimizations are **POST-MVP / PLANNED** unless explicitly marked as implemented.

## Purpose
Define performance targets, measurement methods, and optimization techniques for AKWB analysis and workspace generation.

## Responsibilities
- Set latency and throughput targets.
- Define concurrency and streaming approaches.
- Specify memory and disk budgets.
- Identify caching and indexing strategies.
- Provide profiling and observability hooks.

## Targets
- **Cold analysis:** 1M LOC project in under five minutes on a modern laptop. **Target for post-MVP benchmarking; not verified in 1.0.0 MVP.**
- **Incremental update:** under 30 seconds for fewer than 100 changed files. **Target for post-MVP benchmarking; not verified in 1.0.0 MVP.**
- **Memory:** under 4 GB peak for 1M LOC; streaming for larger projects. **Target for post-MVP benchmarking; not verified in 1.0.0 MVP.**
- **Disk:** workspace size under 2x source size by default. **Target for post-MVP benchmarking; not verified in 1.0.0 MVP.**
- **Startup:** CLI ready in under one second. **Implemented in 1.0.0 (CLI imports and runs quickly for small projects).**

## Concurrency (POST-MVP / PLANNED)
- Multi-threaded file I/O and fingerprinting. **POST-MVP / PLANNED.**
- Worker pool for parsing and extraction; size is configurable by CPU cores and memory. **POST-MVP / PLANNED.**
- Event-driven pipeline with bounded queues between engines. **POST-MVP / PLANNED.**
- Process pools are preferred where language runtimes or heavy dependencies are involved. **POST-MVP / PLANNED.**

> **1.0.0 MVP Status:** Files and artifacts are processed sequentially.

## Streaming & Bounded Memory (POST-MVP / PLANNED)
- Files are processed as a stream; the entire repository is never loaded into memory. **POST-MVP / PLANNED.**
- JSONL output for append-only collections. **Implemented in 1.0.0 for persistence format; full serialization still materializes buffers in memory (POST-MVP / PLANNED to stream).**
- Large files are processed in chunks or skipped based on `maxFileSize`. **POST-MVP / PLANNED.**
- Prior snapshots are loaded lazily. **POST-MVP / PLANNED.**

> **1.0.0 MVP Status:** Catalogs, graphs, and exports are built as in-memory collections before serialization.

## Caching (POST-MVP / PLANNED)
- Content-addressable parse and extract cache. **POST-MVP / PLANNED.**
- Fingerprint index for fast incremental checks. **Partially implemented in 1.0.0 (fingerprints are computed and stored; cache directories are created but not used for content-addressable parse/extract caching).**
- SQLite indexes for graph queries. **POST-MVP / PLANNED.**
- Plugin-level caches in `cache/parsed/` and `cache/extracted/`. **POST-MVP / PLANNED.**

## Indexing (POST-MVP / PLANNED)
- Inverted keyword index for source and knowledge units. **POST-MVP / PLANNED.**
- Vector index for embeddings (optional). **POST-MVP / PLANNED.**
- Graph adjacency index for relationship traversal. **POST-MVP / PLANNED.**

> **1.0.0 MVP Status:** The graph is held in memory; no persistent or query indexes are built.

## Observability
- Structured logs with phase durations. **Partially implemented in 1.0.0 (text logs emitted; phase durations and correlation IDs are POST-MVP / PLANNED).**
- Metrics: files/sec, units/sec, cache hit rate, peak memory. **POST-MVP / PLANNED.**
- `--profile` flag to dump a timing breakdown. **POST-MVP / PLANNED.**
- Progress reporting with file counts and ETA. **POST-MVP / PLANNED.**

## Inputs
- Product requirements.
- System architecture.
- Engine designs.

## Outputs
- Performance budget.
- Concurrency model.
- Profiling data and reports.

## Dependencies
- `02_PRODUCT_REQUIREMENTS.md`
- `03_SYSTEM_ARCHITECTURE.md`
- `14_INCREMENTAL_ANALYSIS.md`
- `15_STORAGE_MODEL.md`

## Future Extensions
- Distributed or remote worker pools.
- GPU acceleration for embeddings.
- Adaptive chunk sizing based on memory pressure.

## Risks
- Parallel parsing can exhaust memory on very large files.
- Over-indexing can slow writes.
- Cross-platform differences in process and thread scheduling.

## Design Decisions

> **1.0.0 MVP implementation note:** The decisions below describe the intended long-term design. Items implemented in 1.0.0 are noted; others are **POST-MVP / PLANNED.**

- Python-specific: parser worker pools use process pools where possible to avoid GIL contention; I/O-bound work uses threads. **POST-MVP / PLANNED.**
- Bounded queues and backpressure between engines prevent memory spikes when producers outpace consumers. **POST-MVP / PLANNED.**
- Batch sizes for parsing and extraction are configurable and default to a memory-safe chunk (e.g., 100 files or 64 MB, whichever comes first). **POST-MVP / PLANNED.**
- Memory-mapped files are considered for large JSONL reads; writes remain streaming. **POST-MVP / PLANNED.**
- Worker pool size is adaptive: default to logical CPU count, capped by available RAM and `maxWorkers` config. **POST-MVP / PLANNED.**
- Graph size budget triggers spilling to SQLite and lazy loading when in-memory node/edge counts exceed thresholds. **POST-MVP / PLANNED.**
- Streaming by default; aggregation happens only at engine boundaries. **POST-MVP / PLANNED.**
- Cache is content-addressable; no manual invalidation is needed. **POST-MVP / PLANNED.**
- Indexes are built after graph assembly, not per-file. **POST-MVP / PLANNED.**
