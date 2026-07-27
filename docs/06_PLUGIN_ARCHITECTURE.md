# Plugin Architecture

## Purpose
Specify how AKWB can be extended to support new languages, frameworks, extractors, exporters, and integrations without modifying core code.

## Responsibilities
- Define plugin lifecycle and packaging.
- Define extension points (ports) and their contracts.
- Define plugin discovery, loading, configuration, and isolation.
- Define versioning, compatibility, and security rules.

## Extension Points (Ports)
Each plugin declares one or more ports it implements:

1. **Detector:** Identifies project types and classifies files.
2. **Reader:** Converts a source artifact into `NormalizedContent` for non-document content (`text`, `binary`, `structured`, etc.).
3. **DocumentReader:** The canonical parser contract for document artifacts. It emits a `CanonicalDocument` and requires no knowledge of downstream extraction. DOCX, PDF, HTML, email, and other document parsers implement this port.
4. **Segmenter:** Splits `NormalizedContent` into `Segment`s.
5. **Extractor:** Derives `KnowledgeUnit` and `Relationship` objects from parsed content.
6. **RelationshipBuilder:** Adds cross-file, cross-language, or inferred relationships after extraction.
7. **ContextBuilder:** Produces AI context fragments from `KnowledgeUnit`s.
8. **Reporter:** Generates human-readable reports from workspace artifacts.
9. **Exporter:** Serializes graph or workspace data to external formats.
10. **StorageBackend:** Persists artifacts (reserved for future storage backends).

## Plugin Manifest (`plugin.yaml`)
- `id`: reverse-DNS identifier.
- `name`, `version`, `author`, `license`.
- `ports`: list of `{port, priority}` entries.
- `entrypoint`: module, package, or binary path.
- `runtime`: `python`, `wasm`, `executable`, or `script`.
- `dependencies`: other plugins or system tools.
- `config_schema`: JSON Schema for plugin-specific configuration.
- `permissions`: `filesystem`, `network`, `execute`, `secrets`, `out_of_project_read`.
- `signature`: optional cryptographic signature; required for elevated permissions or remote registries.

## Plugin Lifecycle
1. **Discovery:** AKWB scans plugin directories, `AKWB_PLUGIN_PATH`, and optional registries.
2. **Validation:** Manifest schema, signature, and permissions are checked.
3. **Resolution:** Dependency graph is resolved; conflicts are reported.
4. **Instantiation:** DI container creates the plugin instance, injecting `Logger`, `Config`, `StoragePort`, and `EventBus`.
5. **Configuration:** Project config is merged with plugin defaults.
6. **Execution:** Plugin is invoked during the relevant engine phase.
7. **Teardown:** Resources are released; audit logs are flushed.

## Sandbox & Isolation
- By default plugins may only read the project directory and write to `.akwb/` through the storage port.
- Network and subprocess permissions require explicit opt-in and, for network, a valid signature.
- Filesystem access outside the project is blocked via canonical path validation.
- A resource watchdog can terminate plugins that exceed CPU time, memory, or file-size limits.

## Inputs
- Source files and metadata.
- Engine requests (detect, parse, extract, build, report, export).
- Project configuration.
- Plugin manifest, dependencies, and permissions.

## Outputs
- Detected project profiles.
- Parsed representations.
- Knowledge units and relationships.
- Context fragments, reports, and exports.

## Dependencies
- `03_SYSTEM_ARCHITECTURE.md`
- `04_DOMAIN_MODEL.md`
- `05_MODULES.md`

## Future Extensions
- Plugin marketplace with signed distribution.
- WASM-based plugins for portability and stronger sandboxing.
- Remote plugin execution over gRPC/JSON-RPC.
- Plugin composition chains and workflow plugins.

## Risks
- Malicious or buggy plugins crashing the analysis process.
- Plugin API churn causing ecosystem fragmentation.
- Dependency conflicts between plugins.

## Design Decisions

- Plugin packages are distributed as signed directories, wheels, or zip archives with a `plugin.yaml` at the root.
- Plugin runtime isolation is chosen per runtime: Python plugins run in-process by default with path sandboxing; `wasm`/`executable` plugins run in separate processes.
- Plugin API version (`plugin_api_version`) is declared in `plugin.yaml` and checked by core before loading.
- Plugins expose a `capabilities()` or `health()` introspection call for runtime capability discovery.
- Plugin conflict resolution uses port priority plus explicit user overrides in configuration.
- Signature verification uses Sigstore/cosign or minisign; unsigned plugins are allowed only for local development with `pluginSignatureRequired: false`.
- License and author attribution are required fields in `plugin.yaml`.
- Plugin contracts are versioned ports, not generic hooks.
- Manifest declares permissions explicitly; least privilege is the default.
- Core does not depend on plugins; plugins depend on core ports.
- Sandboxing is defense in depth: core validates paths and permissions, with OS-level isolation as an optional layer.
