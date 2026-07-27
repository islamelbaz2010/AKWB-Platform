# Support

This page lists the support resources available for the AKWB Platform.

## Documentation

Start with the documents in the `docs/` directory:

- [`docs/PRODUCT_SCOPE.md`](docs/PRODUCT_SCOPE.md) — what AKWB is and is not.
- [`docs/MVP_ACCEPTANCE_TEST.md`](docs/MVP_ACCEPTANCE_TEST.md) — how to verify a release.
- [`docs/13_CLI_SPECIFICATION.md`](docs/13_CLI_SPECIFICATION.md) — CLI commands and exit codes.
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) — deliberately deferred items.
- [`docs/16_SECURITY_MODEL.md`](docs/16_SECURITY_MODEL.md) — security posture and planned hardening.
- [`docs/17_PERFORMANCE_STRATEGY.md`](docs/17_PERFORMANCE_STRATEGY.md) — performance targets and future optimizations.

## Getting Help

- **Bug reports & feature requests:** open an issue at
  <https://github.com/akwb/akwb-platform/issues>.
- **Questions:** start a discussion in the repository's Discussions tab or open
  an issue labelled `question`.
- **Security issues:** please do not open public issues. Email the maintainers
  directly and include "SECURITY" in the subject line.

## Minimum Environment

- Python 3.12 or newer.
- macOS, Linux, or Windows (paths use `pathlib` internally).
- No network required for the 1.0.0 MVP; external plugins and telemetry are
  opt-in and not implemented in this release.

## Troubleshooting

### `akwb` is not found

Make sure the virtual environment is active and the package is installed in
editable mode:

```bash
pip install -e ".[dev]"
```

### Workspace not found

Run `akwb init .` or `akwb analyze .` in the project root. The `.akwb/` directory
is created next to the project files.

### Analysis produces no objects

AKWB 1.0.0 MVP extracts knowledge from Markdown and Python source files. Other
file types are discovered but skipped by the built-in extractors. Plugins can
extend extraction for additional formats.

## Release Support Policy

Only the latest stable release is supported. Critical fixes are back-ported to
the current minor version when possible. Upgrade instructions are provided in
`docs/UPGRADE_GUIDE.md`.
