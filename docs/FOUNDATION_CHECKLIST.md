# Foundation Checklist

## 1. Purpose

This checklist captures everything that must be in place before the first line of implementation code is written for Sprint 1. It is the **pre-flight checklist** for the AKWB Platform foundation.

## 2. Architecture Freeze Approval

- [ ] `ARCHITECTURE_FREEZE_v1.md` reviewed and approved by all stakeholders.
- [ ] `IMPLEMENTATION_GUIDE.md` reviewed and approved.
- [ ] `SPRINT_1_EXECUTION_PLAN.md` reviewed and approved.
- [ ] No unresolved architecture decisions remain.
- [ ] Architecture Version 1 is formally declared frozen.

## 3. Environment and Tooling

- [ ] Python 3.12 installed on all developer machines.
- [ ] `pyenv` or equivalent Python version manager configured.
- [ ] Virtual environment strategy agreed (e.g., `venv`, `uv`, `poetry`).
- [ ] Git repository initialized with `main` branch protection.
- [ ] `pyproject.toml` template ready (build system, entry points, dev dependencies).
- [ ] Pre-commit hooks configured for `ruff`, `mypy`, and basic checks.
- [ ] CI/CD platform account and runner access (GitHub Actions / equivalent).
- [ ] Cross-platform test environments available (Ubuntu, macOS, Windows).

## 4. Repository Structure

- [ ] `src/akwb/` directory created.
- [ ] `tests/` directory created with subdirectories: `unit`, `engine`, `contract`, `integration`, `security`, `fixtures`.
- [ ] `fixtures/` directory created with placeholders for `python`, `nodejs`, `mixed`, `docs-only`, `large`.
- [ ] `docs/` directory has `architecture/`, `ADRs/`, and `PLUGIN_API_SPEC.md` placeholders.
- [ ] `scripts/` directory created for helper scripts.
- [ ] `.gitignore` excludes `.akwb/`, `__pycache__`, `.venv`, build artifacts.

## 5. Team and Roles

- [ ] Principal Engineer assigned.
- [ ] CLI Lead assigned.
- [ ] Config Lead assigned.
- [ ] Storage Lead assigned.
- [ ] Plugin Lead assigned.
- [ ] Discovery Lead assigned.
- [ ] Security Lead assigned.
- [ ] Test Lead assigned.
- [ ] DevOps Lead assigned.
- [ ] Sprint kickoff scheduled.

## 6. Design Artifacts

- [ ] Final engine list agreed: Discovery, Knowledge, Graph, Memory, AI, Workspace, Incremental.
- [ ] Final module list agreed and documented in `ARCHITECTURE_FREEZE_v1.md`.
- [ ] Final folder structure agreed.
- [ ] Final data flow diagram/sketch reviewed.
- [ ] Final CLI commands and flags agreed.
- [ ] Final plugin API ports and request/response models agreed.
- [ ] Final storage strategy agreed.
- [ ] Final workspace layout agreed.
- [ ] Final output formats and naming conventions agreed.
- [ ] Final configuration model and precedence agreed.

## 7. Security and Compliance

- [ ] Telemetry policy approved: opt-in, off by default, no project data leakage.
- [ ] Plugin permission model approved.
- [ ] Plugin signature strategy approved (Sigstore/cosign or minisign).
- [ ] Secret scanning approach approved.
- [ ] Audit logging requirements approved.
- [ ] Threat model reviewed and accepted.
- [ ] Privacy impact assessment complete (if required by organization).

## 8. External Dependencies

- [ ] Python packaging strategy chosen (wheel, standalone binary via PyInstaller/PEX/Nuitka, Docker).
- [ ] Optional Rust extension strategy decided (deferred until profiling proves need).
- [ ] Embedding model strategy decided: local-first, optional, off by default.
- [ ] No external network dependencies required for Sprint 1.

## 9. Testing and Fixtures

- [ ] Fixture projects identified or created.
- [ ] Golden output format defined.
- [ ] Contract test harness design approved.
- [ ] CI test matrix defined (Python 3.12 on Ubuntu, macOS, Windows).
- [ ] Coverage target set: 100% domain, >80% engines.

## 10. Communication

- [ ] Sprint 1 kickoff meeting held.
- [ ] Daily standup time booked.
- [ ] Architecture question escalation path defined.
- [ ] Definition of Done understood by all team members.
- [ ] Sprint review and demo date scheduled.

## 11. Sign-Off

| Role | Name | Signature / Date |
|---|---|---|
| Chief Software Architect | | |
| Principal Engineer | | |
| Security Architect | | |
| Product Owner | | |
| Tech Lead | | |

## 12. Done Criteria

The foundation is ready when **all** checklist items above are checked and signed off. Only then may Sprint 1 implementation begin.
