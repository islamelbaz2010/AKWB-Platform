# CLI Specification

## Purpose
Define the command-line interface commands, flags, outputs, exit codes, and behavior for the `akwb` CLI.

## Responsibilities
- Define primary and secondary commands.
- Define argument syntax, defaults, and allowed values.
- Define output conventions, progress reporting, and structured output.
- Define exit codes and error handling.

## Primary Commands

> **1.0.0 MVP implementation note:** The commands `version`, `init`, `analyze`, `discover`, `doctor`, `report`, and `export` are implemented. Commands and flags marked **POST-MVP** are documented for planning but not yet available.

### `akwb analyze <path>`
Analyze a project directory and generate or update its `.akwb/` workspace.

Flags:
- `--depth minimal|standard|deep`: override extraction depth. **Implemented in 1.0.0.**
- `--force`: ignore incremental state and perform a full analysis. **Implemented in 1.0.0.**
- `--json`: output structured JSON. **Implemented in 1.0.0.**
- `--config <path>`: use a specific configuration file. **POST-MVP / PLANNED.**
- `--plugin <id>`: load a specific plugin; repeatable. **POST-MVP / PLANNED.**
- `--no-ai`: skip AI context generation. **POST-MVP / PLANNED.**
- `--output <dir>`: write workspace to a custom directory. **POST-MVP / PLANNED.**
- `--format <format>`: report output format. **POST-MVP / PLANNED.**

If `<path>` is omitted, use the current directory.

### `akwb update` (POST-MVP / PLANNED)
Incrementally update the workspace for the project in the current directory.
Equivalent to `akwb analyze .` with incremental mode.

> **1.0.0 MVP Status:** Not implemented. Use `akwb analyze .` (which re-runs the full pipeline) instead.

### `akwb status` (POST-MVP / PLANNED)
Show workspace status: last analysis time, changed files, missing plugins, workspace size.
Flags: `--json`, `--verbose`.

> **1.0.0 MVP Status:** Not implemented.

### `akwb config <key> [<value>]` (POST-MVP / PLANNED)
Get or set configuration values.
- `--global`, `--project` scopes.
- `akwb config --list` dumps the effective configuration.

> **1.0.0 MVP Status:** Not implemented. Configuration is loaded from `akwb.yaml`, `.akwb/config.yaml`, environment variables, and defaults.

### `akwb report <name>`
Generate or re-display a specific report.
Examples: `summary`, `structure`, `graph`.

> **1.0.0 MVP Status:** `summary`, `structure`, and `graph` reports are implemented with `--output`. The `coverage` report and `--format` flag are **POST-MVP / PLANNED.**

### `akwb plugin <subcommand>` (POST-MVP / PLANNED)
- `list`: list loaded and available plugins.
- `install <id>`: install plugin from registry or local path.
- `remove <id>`: remove a plugin.
- `verify`: verify plugin signatures and permissions.

> **1.0.0 MVP Status:** Not implemented. Plugins are loaded automatically from configured `plugins.directories`.

### `akwb clean` (POST-MVP / PLANNED)
Remove workspace artifacts and cache, keeping configuration.
Flags: `--cache-only`, `--all`.

> **1.0.0 MVP Status:** Not implemented. Delete `.akwb/` manually and re-run `akwb analyze .` to regenerate it.

### `akwb version`
Print the AKWB version.

> **1.0.0 MVP Status:** Implemented. It prints the CLI version only; plugin API version and environment details are **POST-MVP / PLANNED.**

## Progress & Output
- Default output: human-readable summary and artifact paths. **Implemented in 1.0.0.**
- `--json` produces structured output suitable for scripting. **Implemented in 1.0.0 for `init`, `analyze`, `discover`, and `doctor`.**
- `--quiet` suppresses progress and informational output. **POST-MVP / PLANNED.**
- `--verbose` increases logging detail. **POST-MVP / PLANNED.**
- Progress bar and summary table. **POST-MVP / PLANNED.**

## Exit Codes
- `0`: success
- `1`: general error
- `2`: invalid configuration
- `3`: unsupported project / no applicable plugins
- `4`: analysis partially failed
- `10`: plugin error

> **1.0.0 MVP Status:** Exit codes `0`, `1`, `2`, `3`, `4`, and `10` are used. Exit code `5` (security / permission error) is documented but not emitted by the MVP implementation.

## Inputs
- User command line.
- Configuration files and environment variables.
- Project directory.

## Outputs
- Console output.
- `.akwb/` workspace.
- Exit code.

## Dependencies
- `01_PRODUCT_VISION.md`
- `02_PRODUCT_REQUIREMENTS.md`
- `12_CONFIGURATION.md`

## Future Extensions
- Interactive mode (`akwb interactive`).
- Shell completions.
- `akwb ask <question>` (RAG chat).
- CI integration (`akwb ci`).

## Risks
- CLI surface expansion could conflict with the one-command vision.
- Inconsistent flag naming across commands.

## Design Decisions

- `akwb init [<path>]` bootstraps a project with a default `.akwb/config.yaml` and recommended `.gitignore` entries. **POST-MVP / PLANNED:** the 1.0.0 MVP creates `workspace.json`, `logs/`, `cache/`, and `staging/` only; users may create `akwb.yaml` or `.akwb/config.yaml` manually.**
- `akwb doctor` validates the environment (plugins, permissions, disk space, config) and reports actionable diagnostics. **1.0.0 MVP Status:** Validates Python version, project-root writability, workspace existence, and plugin-directory paths. Plugin, permission, disk-space, and configuration validation are **POST-MVP / PLANNED.**
- `akwb analyze --check` performs a dry-run that reports what would change without writing artifacts. **POST-MVP / PLANNED.**
- CLI flags that accept lists (`--plugin`, `--ignore`) are repeatable and merged with configuration.
- Environment variables map to dotted keys with the `AKWB_` prefix; CLI flags override environment variables.
- Structured output (`--json`) follows a stable schema versioned with the CLI.
- CLI surface is intentionally small; complex behavior is automatic.
- Default behavior is incremental; `--force` is explicit.
- Human-first output; `--json` is for machines.
- Flags map to configuration dotted keys.
