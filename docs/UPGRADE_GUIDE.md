# AKWB Upgrade Guide — Version 1.0.0 MVP

## Scope

This guide covers upgrading to AKWB **1.0.0 MVP**. Because 1.0.0 is the first
public release, there is no formal migration path from a previous stable
version. This guide is intended for:

- Users installing AKWB for the first time.
- Early adopters who were running pre-release builds from the `main` branch.
- Plugin authors who want to target the 1.0.0 plugin API.

## Installing 1.0.0

### From PyPI

```bash
pip install akwb==1.0.0
```

### From source

```bash
git clone <repository>
cd akwb-platform
pip install -e .
```

### Verify the installation

```bash
akwb version
# Expected output: 1.0.0
```

> **Note:** The source files currently report `0.1.0`. Before the 1.0.0 tag is
> published, the version strings in `src/akwb/_version.py` and `pyproject.toml`
> will be bumped to `1.0.0`.

## First-time setup

For a new project, run the analysis pipeline:

```bash
cd <project-root>
akwb analyze .
```

This will:

1. Initialize `.akwb/` if it does not exist.
2. Discover project artifacts.
3. Extract knowledge objects and relationships.
4. Build the knowledge graph.
5. Write reports and exports to `.akwb/reports/` and `.akwb/graph/`.

### Recommended `.gitignore` entries

Add the following to your project `.gitignore` so that generated workspace
artifacts are not committed:

```gitignore
.akwb/cache/
.akwb/staging/
```

`workspace.json`, catalog, graph, and report files in `.akwb/` may be committed
if you want to share the generated analysis, but they are regenerated on each
`akwb analyze` run.

## Upgrading from pre-release builds

If you previously installed AKWB from source before the 1.0.0 tag:

1. Remove or back up the existing `.akwb/` workspace in each project:

   ```bash
   rm -rf .akwb
   ```

   or

   ```bash
   mv .akwb .akwb.backup
   ```

2. Re-install the package:

   ```bash
   pip install --force-reinstall akwb==1.0.0
   ```

3. Re-run the analysis:

   ```bash
   akwb analyze .
   ```

There is no `akwb migrate` command in 1.0.0. The workspace format is
`workspace-v1` and is forward-compatible within the 1.x series.

## Plugin author changes

- Plugin API version for 1.0.0 is `"1"`.
- A minimal plugin requires a `plugin.yaml` manifest and an `entry_point` module
  exposing a `register(api)` function.
- Plugins declare ports and permissions in `plugin.yaml`. AKWB 1.0.0 loads local
  plugins from directories configured in `plugins.directories` but does not yet
  enforce permission restrictions or signature verification. Plugin authors
  should keep this limitation in mind when distributing plugins.

Example `plugin.yaml`:

```yaml
name: my-plugin
version: 0.1.0
plugin_api_version: "1"
description: Example AKWB plugin
entry_point: plugin
ports:
  - extractor
permissions:
  - filesystem:read
```

Example entry point (`plugin.py`):

```python
def register(api):
    api.register_port("extractor", MyExtractor)
```

## Configuration changes

The effective configuration merges:

1. Built-in defaults
2. `~/.config/akwb/config.yaml`
3. Project `akwb.yaml` or `.akwb/config.yaml`
4. `AKWB_*` environment variables
5. CLI flags

No breaking configuration changes exist for 1.0.0 because there is no previous
release.

## Known compatibility notes

- **Python version:** Python 3.12 or later is required.
- **Operating systems:** Developed and tested on macOS and Linux. Windows may
  work but is not part of the current test matrix.
- **Workspace format:** `workspace-v1`. Future 1.x releases will maintain
  backward compatibility with this format.

## Getting help

- Run `akwb --help` for command-line usage.
- See `docs/MVP_ACCEPTANCE_TEST.md` for the canonical test scenario.
- See `docs/RELEASE_NOTES_v1.0.0.md` and `docs/KNOWN_ISSUES.md` for feature
  details and current limitations.
