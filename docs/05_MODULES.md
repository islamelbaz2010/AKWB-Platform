# Modules

## Purpose
Define the code-level module structure, package boundaries, and responsibilities so that implementation teams can map architecture directly to a source tree.

## Responsibilities
- List top-level modules and submodules.
- State each module's public interface and invariants.
- Enforce Clean Architecture dependency direction.
- Document cross-module interaction rules.

## Top-Level Modules

### `akwb` (root / executable entry point)
- Application entry point, version string, global error handling, signal management.
- Delegates to `akwb.cli`.

### `akwb.cli`
- Argument parsing, command dispatch, progress rendering, exit-code logic.
- Depends on `kernel`, `config`, and `reporting`.

### `akwb.kernel`
- Application orchestrator and use-case coordinator.
- Loads configuration, initializes the DI container, schedules engines, manages lifecycle, and publishes events.
- Depends on `engines`, `domain`, `plugins`, `storage`, and `incremental`.

### `akwb.config`
- Configuration schemas, loading, validation, and merging.
- No domain logic; pure data mapping.

### `akwb.domain`
- Entities, value objects, domain events, repository interfaces, and domain services.
- Allowed dependency: `akwb.types` only.

### `akwb.types`
- Shared type definitions, constants, result types, and serialization primitives.
- No business logic; may be used by any module.

### `akwb.engines`
- Submodules for `discovery`, `knowledge`, `workspace`, and `ai`.
- Each engine implements a port defined in `domain` and publishes events.
- Coordinates through `kernel`; does not depend on specific plugins or CLI.

### `akwb.plugins`
- Plugin loader, registry, lifecycle, sandbox, and contract validation.
- Depends on `domain` ports; loads plugin packages dynamically.

### `akwb.storage`
- Storage backend implementations and local workspace I/O.
- Implements repository interfaces declared in `domain`.

### `akwb.reporting`
- Report rendering and output formatting (human-readable and structured).
- Consumes workspace artifacts, not raw engine state.

### `akwb.incremental`
- Fingerprinting, change detection, invalidation graph, and diff engine.
- Used by `engines` and `workspace`.

### `akwb.security`
- Secret scanning, sandbox enforcement, plugin signature verification, audit logging.
- Cross-cutting concerns used by `plugins`, `storage`, and `engines`.

## Dependency Rules
- `domain` and `types` have no internal AKWB dependencies.
- `engines` depend on `domain`, `types`, `incremental`, and `security` (interfaces where possible).
- `plugins` and `storage` implement `domain` ports.
- `cli` depends only on `kernel`, `config`, and `reporting`.
- No circular dependencies are permitted.

## Inputs
- System architecture.
- Domain model.
- Plugin architecture.

## Outputs
- Module inventory.
- Dependency map.
- Implementation directory guidelines.

## Dependencies
- `03_SYSTEM_ARCHITECTURE.md`
- `04_DOMAIN_MODEL.md`
- `06_PLUGIN_ARCHITECTURE.md`

## Future Extensions
- Language-specific plugin SDKs (`akwb-plugin-python`, `akwb-plugin-node`, etc.).
- Standalone server module (`akwb.server`).
- GUI/IDE bridge modules.

## Risks
- Package creep; strict boundaries are required.
- Plugin SDKs may duplicate types if core `types` are not versioned carefully.

## Design Decisions

- Add `akwb.events` as a lightweight, typed event bus shared by `kernel` and `engines`.
- Add `akwb.observability` for logging, metrics, diagnostics, and progress reporting; it may be used by all modules.
- Add `akwb.unit_of_work` to implement the domain `UnitOfWork` port and coordinate `storage` transactions.
- Keep `akwb.types` as a shared kernel for result types, serialization primitives, and constants to avoid circular imports.
- Future: `akwb.query` for graph query APIs and `akwb.graph` for graph algorithms when they outgrow `knowledge`.
- One top-level module per bounded context / Clean Architecture layer.
- Engines are submodules of a single package for shared event dispatch and scheduling.
- Repository interfaces live in `domain` so storage and engines remain decoupled.
- `akwb.types` is a lightweight shared kernel to avoid circular dependencies.
