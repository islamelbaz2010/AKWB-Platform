# Testing Strategy

## Purpose
Define how AKWB and its plugins are tested at multiple levels to ensure correctness, stability, and contract compliance.

## Responsibilities
- Define test levels and scopes.
- Define fixture projects and golden outputs.
- Define plugin contract tests.
- Define performance and compatibility testing.
- Define CI/CD testing gates.

## Test Levels

### 1. Unit Tests
- Test individual domain entities, value objects, utilities, and algorithms.
- No I/O; use in-memory fakes.
- Fast feedback, target under one minute.

### 2. Engine Tests
- Test Discovery, Knowledge, Workspace, and AI engines with fixture projects.
- Use in-memory storage and stub plugins.
- Validate event ordering and output artifacts.

### 3. Plugin Contract Tests
- Each plugin is tested against its port contract using standard fixtures.
- Golden outputs for parse, extract, and context builders.
- Version compatibility matrix.

### 4. Integration Tests
- End-to-end analysis of real open-source repositories (cached locally).
- Cross-platform runs in CI (Windows, macOS, Linux).
- Incremental correctness validated by diffing snapshots.

### 5. Performance / Benchmark Tests
- Run against `fixtures/large` projects.
- Track files/sec, memory, and latency regressions.
- Fail on >10% regression without explicit approval.

### 6. Security Tests
- Malformed plugin manifests.
- Secret scanning patterns.
- Sandbox escape attempts.
- Permission enforcement.

## Fixtures
- `fixtures/python/django-style`
- `fixtures/nodejs/express`
- `fixtures/mixed`
- `fixtures/docs-only`
- Each fixture includes expected `SourceCatalog`, `KnowledgeGraph`, and report snapshots.

## Acceptance Criteria
- All tests pass before release.
- Plugin contract tests pass for all bundled plugins.
- New plugin ports require contract test fixtures.
- 100% unit test coverage for the domain layer; target >80% for engines.

## Inputs
- Product requirements.
- Engine designs.
- Plugin architecture.

## Outputs
- Test suite and fixtures.
- Coverage and benchmark reports.
- CI gates.

## Dependencies
- `03_SYSTEM_ARCHITECTURE.md`
- `06_PLUGIN_ARCHITECTURE.md`
- `07_DISCOVERY_ENGINE.md`
- `08_KNOWLEDGE_ENGINE.md`
- `14_INCREMENTAL_ANALYSIS.md`

## Future Extensions
- Fuzz testing of parsers.
- Chaos testing for plugin failures.
- LLM-based evaluation of context quality.

## Risks
- Fixture maintenance cost.
- Flaky integration tests due to network or tool versions.
- Plugin contract changes ripple through the ecosystem.

## Design Decisions

- CI runs unit, engine, contract, integration, performance, and security tests on Ubuntu, macOS, and Windows.
- A plugin contract test harness runs every loaded plugin against port-specific fixtures and golden outputs.
- A benchmarking harness measures cold and incremental analysis on `fixtures/large` and fails on >10% regression.
- Property-based and mutation tests target parsers, extractors, and fingerprinting logic.
- Plugin SDK tests validate that example plugins load, execute, and report diagnostics correctly.
- Security tests verify sandbox escape attempts and secret redaction in generated artifacts.
- Domain layer is fully unit-tested; engines and integration use fixtures.
- Golden snapshots are stored as artifacts for deterministic regression detection.
- Contract tests are required for plugin marketplace acceptance.
- A mock storage backend is used for tests to avoid filesystem flakiness.
