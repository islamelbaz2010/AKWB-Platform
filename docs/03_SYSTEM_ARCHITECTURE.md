# System Architecture

## Purpose
Describe the high-level structure, component boundaries, data flow, and deployment view of AKWB so that implementers understand how pieces fit together.

## Responsibilities
- Define Clean Architecture layers and major components.
- Show how data flows from raw project files to a populated workspace.
- Identify runtime, design-time, and deployment concerns.
- Establish dependency direction and coupling rules.

## Architecture Overview
AKWB is a single CLI process composed of a kernel and four cooperating engines. It follows Clean Architecture: the domain sits at the center, surrounded by application engines, adapters (plugins, CLI, storage), and infrastructure (filesystem, optional network).

### Layers (inside-out)
1. **Domain Layer:** Entities, value objects, domain events, repository interfaces, and domain services. Pure; no framework or filesystem dependencies.
2. **Application Layer:** Use cases orchestrated by the kernel and engines. Coordinates plugins through domain ports.
3. **Adapter Layer:** Plugin system, CLI commands, storage backends, report renderers, and AI adapters.
4. **Infrastructure Layer:** OS/filesystem, process execution, optional network, logging, and metrics.

### Major Components
- **Kernel:** Parses CLI input, loads and merges configuration, initializes the DI container, schedules engines, and handles lifecycle.
- **Discovery Engine:** Scans the filesystem, detects project profiles, classifies sources, and emits `SourceDiscovered` / `SourceClassified` events.
- **Knowledge Engine:** Parses sources, extracts entities and relationships, builds the `KnowledgeGraph`.
- **Workspace Engine:** Materializes artifacts into `.akwb/` (indexes, reports, graph exports, memory, context).
- **AI Engine:** Summarizes, chunks, embeds, and assembles AI context bundles.
- **Incremental Manager:** Compares fingerprints, computes change sets, and propagates invalidation.

## Data Flow
1. CLI receives command and project path.
2. Configuration is merged from defaults, global config, project config, and CLI flags.
3. Kernel loads plugins, validates permissions, and initializes storage.
4. Discovery Engine walks the project and produces a `SourceCatalog`.
5. Knowledge Engine consumes the catalog, runs parser and extractor plugins, and produces a `KnowledgeGraph`.
6. AI Engine reads the graph and creates context bundles, summaries, and vector indexes.
7. Workspace Engine serializes all artifacts and updates the workspace manifest.
8. Incremental Manager invalidates stale artifacts and prunes obsolete files.

## Inputs
- CLI command and arguments.
- Project directory.
- Configuration files and CLI flags.
- Plugin registry and manifests.
- Previous workspace state.

## Outputs
- Updated `.akwb/` workspace.
- Console output, reports, and exit code.
- Structured logs and audit records.

## Dependencies
- `01_PRODUCT_VISION.md`
- `02_PRODUCT_REQUIREMENTS.md`
- `04_DOMAIN_MODEL.md`
- `05_MODULES.md`
- `06_PLUGIN_ARCHITECTURE.md`

## Future Extensions
- Server mode exposing REST/gRPC APIs.
- Distributed analysis with remote worker pools.
- Cloud storage backends.
- Watch-mode daemon for continuous incremental updates.

## Risks
- Tight coupling between engines if events are misused as command channels.
- Performance bottleneck in Knowledge Engine parsing large files.
- Cross-platform path and process handling complexity.

## Design Decisions

- Introduce an in-process **Event Bus** as a first-class component for typed domain events and engine decoupling.
- Add a **Unit of Work** port to coordinate atomic commits across repositories during an analysis run.
- Add an **Observability / Diagnostics** component for structured logging, metrics, progress events, and plugin diagnostics.
- Define explicit transaction boundaries: workspace artifacts are only promoted after all engines succeed or rolled back on failure.
- Keep external brokers, distributed workers, and watch-mode as future adapters, not core dependencies.
- Clean Architecture with dependency rule pointing inward; outer layers depend on inner layers, never the reverse.
- Event-driven internal coordination for decoupling, not an external message broker.
- In-process CLI; no daemon required for the first releases.
- Project-owned `.akwb/` directory as the workspace boundary.
- Dependency injection container resolves engines, plugins, and storage backends from configuration.
