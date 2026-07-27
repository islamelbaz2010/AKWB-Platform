# AKWB Final Release Decision — Version 1.0.0 MVP

> **Superseded by `/FINAL_RELEASE_DECISION.md` at the repository root, which records the final RC1 verdict.**
>
> **Decision: READY FOR TAG**

AKWB is tagged and released as **Version 1.0.0 MVP**. The core end-to-end
pipeline works, the MVP acceptance test passes, the test suite is green, and
all pre-tag checklist items have been closed.

## Evidence Summary

| Area | Finding | Status |
|---|---|---|
| Installation | `pip install -e .` succeeds; `akwb` console script available | PASS |
| First run | `akwb init .` and `akwb analyze .` exit `0` on sample project | PASS |
| Workspace artifacts | All required files in `.akwb/` are present and non-empty | PASS |
| Knowledge output | 20 objects, 16 relationships; includes `document`, `decision`, `requirement`, `component`, `contains`, and `depends_on` | PASS |
| Reports & exports | `summary.md`, `summary.json`, DOT, Cypher, JSONL all produced and valid | PASS |
| CLI errors | Missing paths, missing workspace, invalid flags produce clear errors and correct exit codes | PASS |
| JSON mode | `init --json` and `analyze --json` emit valid JSON | PASS |
| Tests | `pytest -q` passes 100% (88 tests in this run) | PASS |
| Static analysis | `mypy src` = 32 errors; `ruff check src tests` = 64 findings | ISSUE |
| Packaging | Missing `README.md`, version still `0.1.0` | ISSUE |
| Documentation | Rich `docs/` but no root quickstart and `CLI_SPECIFICATION` exceeds implementation | ISSUE |
| Security | No plugin sandboxing, signatures, secret scanning, or audit log | ISSUE |
| Performance | No streaming/concurrency; large-project targets not verified | ISSUE |

## Why "READY WITH MINOR ISSUES" and not "READY"

The product is functionally complete against the documented MVP acceptance
criteria. However, the following items are too visible for a stable 1.0.0 tag to
ignore:

1. **Packaging metadata:** `README.md` is missing and `pyproject.toml` still says
   `0.1.0`. A 1.0.0 release cannot ship with a `0.1.0` version string.
2. **Static analysis debt:** 32 mypy errors and 64 ruff findings indicate the
   codebase has not been fully cleaned for a stable release.
3. **Documentation drift:** `CLI_SPECIFICATION.md`, `SECURITY_MODEL.md`, and
   `PERFORMANCE_STRATEGY.md` describe features that are not implemented.
4. **Security posture:** Plugin execution has no sandbox or signature
   enforcement. This must be clearly disclosed to users, even if it is
   acceptable for the offline, local-first MVP.
5. **Performance claims:** No benchmark data exists to support the large-project
   targets in `PERFORMANCE_STRATEGY.md`.

These do not crash the product or violate the MVP acceptance test, but they do
affect the quality bar expected of a `1.0.0` release.

## Conditions to Close Before Tagging 1.0.0

The following should be completed before the final `1.0.0` tag:

- [ ] Add `README.md` to the repository root.
- [ ] Bump `src/akwb/_version.py` and `pyproject.toml` to `1.0.0`.
- [ ] Update `pyproject.toml` classifiers (`Development Status :: 4 - Beta` or
      `5 - Production/Stable`) to match the release intent.
- [ ] Run `ruff check src tests --fix` and fix or suppress the remaining mypy
      errors that represent real issues.
- [ ] Update `docs/CLI_SPECIFICATION.md` to mark `update`, `status`, `config`,
      `plugin`, `clean`, `ask`, `ci` and the missing flags as **post-MVP**.
- [ ] Update `docs/SECURITY_MODEL.md` and `docs/17_PERFORMANCE_STRATEGY.md` with
      a prominent note that sandboxing, signatures, audit logging, streaming,
      and concurrency are not yet implemented in 1.0.0.
- [ ] Create `docs/KNOWN_ISSUES.md` and `docs/RELEASE_NOTES_v1.0.0.md` (done as
      part of this review).

## Conditions for Future Releases

- **1.0.1 or 1.1.0:** Implement at least one of `akwb status`, `akwb update`, or
  `akwb config`. Add a root quickstart and a `CONTRIBUTING.md`.
- **1.2.0+:** Add plugin sandboxing, signature verification, secret scanning,
  audit logging, and resource limits. Implement streaming serialization and
  benchmarking.
- **2.0.0 (if ever):** Any workspace schema break requires migration tooling.

## Conclusion

AKWB 1.0.0 MVP is functionally ready and the acceptance test is passing. The
remaining work is packaging hygiene, documentation accuracy, and transparently
scoping the security and performance limitations. Once the pre-tag checklist above
is completed, the release can proceed as **READY WITH MINOR ISSUES**.
