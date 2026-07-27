# Configuration

## Purpose
Define how AKWB is configured at global, project, plugin, and CLI levels, and how settings are validated, merged, and applied.

## Responsibilities
- Define configuration schemas and sections.
- Specify precedence and merging rules.
- Define validation rules and user-facing error messages.
- Provide environment variable and CLI flag mapping.
- Allow plugin-specific configuration without core changes.

## Configuration Sources (lowest to highest precedence)
1. Built-in defaults (`akwb.defaults.yaml`).
2. Global user config (`~/.config/akwb/config.yaml` or `%APPDATA%\akwb\config.yaml`).
3. Project config (`.akwb/config.yaml` in the project, or `akwb.yaml` at project root).
4. CLI flags and environment variables.

## Core Configuration Sections

### `discovery`
- `ignorePatterns`: array of gitignore-style strings.
- `includePatterns`: optional whitelist.
- `maxFileSize`: maximum file size in bytes to analyze.
- `maxDepth`: maximum directory depth.
- `followSymlinks`: boolean.
- `useGitignore`: boolean.

### `knowledge`
- `extractionDepth`: `minimal`, `standard`, or `deep`.
- `enabledExtractors`: list of extractor plugin ids.
- `relationshipConfidenceThreshold`: 0.0–1.0.
- `parseTimeout`: seconds.

### `ai`
- `embeddingModel`: model identifier or path.
- `tokenBudget`: default token budget for context bundles.
- `chunkSize`: target chunk size in tokens.
- `chunkOverlap`: overlap tokens between chunks.
- `enableEmbeddings`: boolean.
- `contextBuilders`: list of builder plugin ids.

### `workspace`
- `outputFormats`: `jsonl`, `dot`, `cypher`, `markdown`.
- `enabledReports`: list of report names.
- `keepLogs`: number of log files to retain.
- `versioning`: `latest` or `snapshot`.

### `plugins`
- `pluginPath`: list of directories to scan.
- `registryUrl`: optional; disabled by default.
- `autoLoad`: boolean.
- `plugins`: map of plugin id to plugin-specific config.

### `security`
- `allowNetwork`: default `false`.
- `allowExecute`: default `false`.
- `secretScanning`: default `true`.
- `pluginSignatureRequired`: default `false`.

## Validation
- Schema validation using JSON Schema / Pydantic / equivalent.
- Unknown keys under plugin sections are allowed when the plugin provides a schema.
- Invalid configuration fails fast before analysis begins.

## Inputs
- Product requirements.
- CLI specification.
- Plugin manifests and schemas.

## Outputs
- Merged effective configuration.
- Configuration snapshot stored in workspace.
- Validation errors and warnings.

## Dependencies
- `02_PRODUCT_REQUIREMENTS.md`
- `13_CLI_SPECIFICATION.md`
- `06_PLUGIN_ARCHITECTURE.md`

## Future Extensions
- Remote configuration and team policies.
- Encrypted secrets in configuration.
- Configuration UI / wizard.

## Risks
- Overlapping ignore patterns confuse users.
- Plugin configuration is not validated by core if schemas are missing.
- Environment-specific paths break portability.

## Design Decisions

- Environment variables map to dotted config keys using the prefix `AKWB_` (e.g., `AKWB_DISCOVERY_MAX_FILE_SIZE`).
- `configVersion` is stored in every effective configuration snapshot to detect incompatible project configs.
- Built-in default ignore patterns are shipped in `akwb.defaults.yaml` and can be overridden or disabled per project.
- Plugin-specific configuration is validated against the plugin's `config_schema`; missing schemas produce warnings, not hard failures.
- YAML is the primary configuration format; TOML and JSON are supported for user preference.
- A configuration snapshot is stored in the workspace for reproducibility.
- Project config can live in `.akwb/config.yaml` (workspace-owned) or `akwb.yaml` (project-owned); both are project data.
- CLI flags map one-to-one to dotted configuration keys where possible.
