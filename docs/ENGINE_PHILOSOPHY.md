# AKWB Engine Philosophy

**Version:** 1.0
**Status:** Ratified with the AKWB Constitution

This document explains the philosophy behind the AKWB Constitution. It is not a
specification. It describes why AKWB is designed the way it is and why the
project rejects certain kinds of growth.

---

## 1. The Problem of Re-Implementation

Every enterprise software project contains knowledge: what the project does,
why decisions were made, how components relate, what depends on what, and what
contracts the system exposes. This knowledge is trapped in source code,
documentation, issue trackers, configuration files, and the heads of the people
who built it.

Downstream products—AI assistants, dashboards, search engines, documentation
sites, code review tools, and analytics platforms—need access to this
knowledge. Today, each product re-implements its own discovery, parsing, and
extraction. The result is duplicated effort, inconsistent results, and fragile
adapters.

AKWB exists to do this once. It is a shared foundation. It does not replace
downstream products; it makes them better.

---

## 2. Why an Engine, Not a Platform

An engine is a tool that transforms input into a reusable artifact. A platform
tells people what to do. AKWB is an engine because:

- **Specialization.** Building a great extraction engine and building a great
  user experience require different skills and different release cycles.
- **Reuse.** An engine can serve many products. A platform usually serves one.
- **Ownership.** The project owns its `.akwb/` workspace. A platform would own
  the data.
- **Neutrality.** AKWB does not favor one downstream product over another. It
  exports facts; products compete on experience.
- **Focus.** The narrower the scope, the better the engine. Every feature added
  to the engine is a feature taken away from a downstream product.

---

## 3. Why Local First

AKWB runs where the project lives. This is not an implementation detail. It is
a moral and architectural stance.

- **Privacy.** Source code is sensitive. It should not leave the project unless
  the owner explicitly chooses.
- **Reproducibility.** Local analysis can be repeated by anyone with the code.
- **No Lock-In.** If the AKWB service disappears, the project still has its
  workspace.
- **Determinism.** Local files and local computation are easier to make
  deterministic.
- **Speed.** Reading local files is faster than uploading them to a service.

External services are not forbidden, but they are never required. Network
access is opt-in and explicit.

---

## 4. Why Project Owned

The `.akwb/` directory belongs to the project, not to AKWB the engine, not to a
company, and not to a cloud service. This matters because:

- **Portability.** The workspace travels with the repository.
- **Versioning.** The workspace can be checked into git, ignored, or archived
  like any other artifact.
- **Transparency.** The project owner can inspect, diff, and delete the
  workspace.
- **Contract.** Downstream products know where to look.

Project ownership is the reason the engine does not hide state in global
caches, home directories, or remote databases.

---

## 5. Why CLI First

A command-line interface is the smallest stable surface. It is scriptable,
testable, and easy to integrate into CI. It does not demand a framework, a
runtime, or a UI toolkit.

The CLI is deliberately small. The primary command is `akwb analyze`. The
secondary commands support inspection and maintenance. AKWB does not grow a
large CLI to avoid becoming a platform by another name.

---

## 6. Why Boundaries Are Harder Than Features

It is easier to add a feature than to remove one. It is easier to build a
chatbot than to say no. It is easier to add an embedding store than to keep the
engine focused. AKWB chooses boundaries because:

- **Clarity.** A narrow product is understood by everyone.
- **Quality.** Fewer responsibilities mean deeper quality per responsibility.
- **Trust.** Downstream products trust the engine more when it does not compete
  with them.
- **Maintenance.** Smaller scope is cheaper to maintain over years.

The Constitution exists because product boundaries erode without permanent
rules.

---

## 7. Why Evidence Before Inference

AKWB claims must be grounded. If it says module A imports module B, it must
point to the import statement. If it says a document describes a component, it
must provide the span. If it infers something with uncertainty, it must say so.

This principle protects downstream products from confidently propagating
hallucinated or weak knowledge. It also makes the workspace debuggable.

Evidence is not an afterthought. It is the foundation of trust.

---

## 8. Why Plugin-Based Extensibility

No single team can support every language, framework, and enterprise format.
Plugin-based design lets the community extend the engine without fracturing it.

But plugins must respect the engine. They do not modify it. They do not depend
on its internals. They implement public ports. This keeps the core stable while
allowing the ecosystem to grow.

Built-in implementations are themselves plugins. The engine does not give
itself special privileges. This symmetry is essential for fairness and
replaceability.

---

## 9. Why Determinism and Reproducibility Matter

A downstream product cannot trust a knowledge engine that produces different
results every time it runs. Non-determinism breaks caching, testing, reviews,
and audits.

AKWB commits to determinism. The same source, the same configuration, and the
same plugins produce the same workspace. Randomness, network calls, and timing
must not change outputs. Where non-determinism is unavoidable, it is declared
and isolated.

---

## 10. Why the Workspace Is the Contract

The `.akwb/` directory is the boundary between AKWB and the world. It is the
only thing downstream products are allowed to depend on. This separation is the
most important architectural decision in the project.

It allows AKWB to refactor, rewrite, and evolve internally without breaking
consumers. It allows downstream products to read the workspace with any tool,
in any language, on any platform.

Internal classes are not a contract. File formats are.

---

## 11. Why We Reject Feature Pressure

AKWB will receive many requests to add features that sound reasonable:
summaries, chat, dashboards, marketplace, cloud sync, workflow triggers, and
more. Each request will be evaluated against the Constitution.

The default answer is no. A yes requires proof that the feature is essential to
the engine mission, cannot live downstream, and does not violate any article.

This is not hostility to innovation. It is the discipline required to build
something that lasts.

---

## 12. The Long-Term Goal

The goal of AKWB is to become the standard knowledge compiler for enterprise
projects. It should be as normal for a project to have a `.akwb/` directory as
it is to have a `.git/` directory.

If AKWB succeeds, every downstream product will be able to understand a project
without re-implementing discovery, parsing, and extraction. The engine will be
small, stable, and universally trusted.

That future depends on refusing to become a platform today.
