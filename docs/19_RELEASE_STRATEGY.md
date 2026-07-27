# Release Strategy

## Purpose
Define how AKWB, its plugins, and the plugin marketplace are versioned, packaged, and distributed to users.

## Responsibilities
- Define the versioning scheme.
- Define distribution channels and artifacts.
- Define release channels (stable, beta, canary).
- Define plugin compatibility and migration rules.
- Define rollback and support policy.

## Versioning
- AKWB CLI follows Semantic Versioning (SemVer).
- The plugin API is versioned independently (`plugin_api_version`).
- Plugins declare a compatible `akwb` version range.
- The workspace format is versioned separately for backward compatibility.

## Distribution Channels
- **PyPI / pipx:** primary installation for Python-based environments.
- **Homebrew** (macOS/Linux), **Scoop** (Windows), **APT/YUM** (Linux).
- **Docker:** `akwb/akwb` image with bundled plugins.
- **Standalone binaries:** built with PyInstaller/PEX/Nuitka for environments without Python.

## Release Channels
- **stable:** production-ready, default.
- **beta:** pre-release for early adopters; opt-in.
- **canary:** nightly or per-merge builds for CI dogfooding.

## Plugin Marketplace
- Remote registry is optional and disabled by default.
- Plugins are signed by authors; the marketplace verifies signatures.
- Compatibility matrix tracks plugin API version vs AKWB version.
- `akwb plugin install <id>` fetches from the registry when enabled.

## Compatibility & Migration
- Workspace format migration scripts are provided for major version bumps.
- Plugin API deprecations include at least one minor version warning.
- `akwb migrate` command (future) upgrades a workspace.

## Rollback
- Keep the previous `workspace.json` manifest; `akwb clean` and re-analysis with a previous version is possible.
- Revert the release via package manager if needed.

## Inputs
- CI/CD pipeline results.
- Test and QA results.
- Marketplace and packaging decisions.

## Outputs
- Release artifacts.
- Changelog and migration guide.
- Marketplace metadata.

## Dependencies
- `18_TESTING_STRATEGY.md`
- `13_CLI_SPECIFICATION.md`
- `06_PLUGIN_ARCHITECTURE.md`

## Future Extensions
- Auto-update checks.
- Enterprise on-premise marketplace.
- Long-term support (LTS) releases.

## Risks
- Plugin API breaks cause ecosystem churn.
- Workspace format migrations are complex.
- Multi-platform packaging failures.

## Design Decisions

- The release pipeline builds, signs, and tests artifacts for PyPI, Homebrew, Scoop, Docker, and standalone binaries in CI.
- Every release produces an SBOM and a signed attestation for supply-chain transparency.
- Reproducible builds are targeted for standalone binaries; Python wheel builds are deterministic.
- Release artifacts (binaries, Docker images, plugin packages) are signed with the project release key.
- Changelogs and migration guides are generated from conventional commits and PR labels.
- Beta and canary channels publish automatically from protected branches; stable releases require manual approval.
- CLI SemVer; plugin API and workspace format independently versioned.
- Distribution is packaging-agnostic: same core, different wrappers.
- Marketplace is opt-in; no network by default.
- Migrations are explicit, not automatic.
