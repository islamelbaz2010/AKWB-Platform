# Contributing to AKWB

Thank you for your interest in AKWB. This project uses a port-driven, clean
architecture and follows Python 3.12 conventions.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs `pytest`, `ruff`, `mypy`, and the `types-PyYAML` stub package.

## Running Checks

```bash
pytest -q
ruff check src tests
mypy src
```

## Project Structure

- `src/akwb/` — core source code.
- `docs/` — architecture, design, and user documentation.
- `tests/` — unit and integration tests.
- `fixtures/` — sample projects used by tests and examples.

## Coding Conventions

- Use `pathlib.Path` for filesystem paths.
- Prefer Pydantic `BaseModel` or frozen dataclasses for value objects.
- Core engines must not import `cli` or `kernel`.
- All public functions and methods should have type hints; the target is
  `mypy --strict`.
- Avoid `print` in core code; emit diagnostics through `akwb.observability`.
- Use `Result[T, Diagnostic]` for operations that can partially fail.

## Adding Tests

- Place unit tests in `tests/unit/<module>/`.
- Place integration tests in `tests/integration/`.
- Add fixtures under `tests/fixtures/` for golden-output comparisons.

## Pull Requests

1. Open an issue describing the bug or enhancement.
2. Create a branch from `main`.
3. Ensure `pytest`, `ruff`, and `mypy` pass locally.
4. Update documentation if the change affects public behaviour.
5. Keep changes focused and minimal.

## Release Process

Releases follow [Semantic Versioning](https://semver.org). A release candidate
is cut from `main`, validated by `pytest`, `ruff`, `mypy`, and the MVP
acceptance test before the `v{major}.{minor}.{patch}` tag is applied.
