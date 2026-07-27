# Security Model

> **1.0.0 MVP implementation note:** This document describes the long-term security architecture. In AKWB 1.0.0 MVP, analysis is local-first and telemetry is disabled by default. Plugin sandboxing, signature verification, secret scanning, audit logging, and resource limits are **POST-MVP / PLANNED** unless explicitly marked as implemented.

## Purpose
Define how AKWB protects project data, limits plugin privileges, prevents secret leakage, and operates safely in untrusted environments.

## Responsibilities
- Define trust boundaries.
- Define plugin sandbox and permission model.
- Define secret scanning and redaction rules.
- Define audit logging.
- Define user data ownership and privacy guarantees.

## Trust Boundaries
- **AKWB Core:** Trusted code released by maintainers.
- **Plugins:** Third-party or community code; must declare permissions and be signed for elevated privileges.
- **Project Data:** Owned by the user; AKWB only reads and writes within the project directory and `.akwb/`.
- **External Services:** No network by default; opt-in per plugin.

## Plugin Security
- **Permission Model:**
  - `filesystem` (read project directory) — declared in `plugin.yaml` in 1.0.0; **not enforced at runtime (POST-MVP / PLANNED).**
  - `network` (requires signature and explicit opt-in) — **POST-MVP / PLANNED.**
  - `execute` (subprocess) — **POST-MVP / PLANNED.**
  - `secrets` (bypass secret redaction) — **POST-MVP / PLANNED.**
  - `out_of_project_read` (read outside the project) — **POST-MVP / PLANNED.**
- **Sandbox:** Canonical path validation **implemented in `LocalStorageBackend` in 1.0.0**; OS sandbox or containerization is **POST-MVP / PLANNED.**
- **Signatures:** Required for plugins requesting `network` or from remote registries. **POST-MVP / PLANNED.**
- **Resource Limits:** CPU time, memory, file size, and network rate limits enforced by watchdog. **POST-MVP / PLANNED.**

## Secret Scanning (POST-MVP / PLANNED)
- Built-in secret scanner in the Discovery Engine flags likely secrets, tokens, and credentials. **POST-MVP / PLANNED.**
- Secrets are redacted from logs, reports, context artifacts, and graph exports. **POST-MVP / PLANNED.**
- Users can configure additional patterns. **POST-MVP / PLANNED.**

## Data Privacy
- All analysis is local by default. **Implemented in 1.0.0.**
- No telemetry unless explicitly enabled. **Implemented in 1.0.0 (telemetry is disabled by default).**
- Workspace data stays in the project directory. **Implemented in 1.0.0.**
- If external AI or embedding models are used, data is sent only with explicit opt-in. **POST-MVP / PLANNED (AI/embedding support is not in 1.0.0).**

## Audit Logging (POST-MVP / PLANNED)
`logs/audit.log` records:
- Plugin load and unload events. **POST-MVP / PLANNED.**
- Network requests (if any). **POST-MVP / PLANNED.**
- External process execution. **POST-MVP / PLANNED.**
- Configuration changes. **POST-MVP / PLANNED.**
- Security violations and sandbox denials. **POST-MVP / PLANNED.**

> **1.0.0 MVP Status:** Only `logs/analysis.log` is produced. Audit logging is not implemented.

## Inputs
- Configuration.
- Plugin manifests and signatures.
- Source files.

## Outputs
- Audit log.
- Redacted artifacts.
- Security diagnostics and warnings.

## Dependencies
- `06_PLUGIN_ARCHITECTURE.md`
- `07_DISCOVERY_ENGINE.md`
- `12_CONFIGURATION.md`

## Future Extensions
- Full plugin isolation via WASM or containers.
- Signed workspace artifacts.
- Enterprise policy enforcement.
- SBOM and vulnerability scanning of plugins.

## Risks
- A plugin with `network` permission could exfiltrate data.
- Secret scanning has false positives and false negatives.
- Overly restrictive defaults may frustrate plugin authors.

## Design Decisions

> **1.0.0 MVP implementation note:** The decisions below describe the intended long-term design. Items implemented in 1.0.0 are noted; others are **POST-MVP / PLANNED.**

- Signature verification uses Sigstore/cosign or minisign; remote plugins must be signed, local dev plugins may be unsigned. **POST-MVP / PLANNED.**
- Audit log entries are append-only and integrity-protected with chained hashes to detect tampering. **POST-MVP / PLANNED.**
- Telemetry and error reporting are opt-in only; no network calls are made without explicit user consent. **Implemented in 1.0.0 (telemetry is disabled by default).**
- Runtime isolation: Python plugins run in-process with path sandboxing; `wasm`/`executable` plugins run in separate processes; high-risk plugins run in OS sandboxes when available. **1.0.0 uses in-process plugins with filesystem path sandboxing only; further isolation is POST-MVP / PLANNED.**
- A resource watchdog enforces CPU time, memory, and file-size limits and can terminate misbehaving plugins. **POST-MVP / PLANNED.**
- Secret scanning combines regex patterns, entropy analysis, and known secret prefixes; matches are redacted in all artifacts. **POST-MVP / PLANNED.**
- Least privilege by default; explicit opt-in for risky permissions. **POST-MVP / PLANNED (permissions are declared but not enforced in 1.0.0).**
- Sandbox is defense in depth; core also validates paths and permissions. **Path validation implemented in 1.0.0; permission enforcement POST-MVP / PLANNED.**
- Secret redaction applies to all artifacts, not just reports. **POST-MVP / PLANNED.**
- Audit log is append-only and, in the future, tamper-evident with chained hashes. **POST-MVP / PLANNED.**
