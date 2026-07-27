# AKWB Downstream Contract

**Version:** 1.0
**Status:** Ratified with the AKWB Constitution

This document is the official contract between AKWB and any product, tool, or
service that consumes its output. It defines what downstream products may
assume, what they must not do, and how the contract evolves.

---

## 1. Purpose

AKWB transforms enterprise projects into a `.akwb/` workspace. Downstream
products consume that workspace. This contract ensures the relationship is
stable, predictable, and fair.

AKWB promises to produce well-defined, versioned artifacts. Downstream products
promise to consume only those artifacts and not depend on the internal
implementation of AKWB.

---

## 2. The Workspace Is the Contract

The only supported integration surface is the `.akwb/` directory.

Downstream products may:

- Read files inside `.akwb/`.
- Parse artifacts according to their documented schemas.
- Depend on the schema version declared in each artifact.
- Watch `.akwb/` for changes.
- Copy or archive `.akwb/` for portability.

Downstream products must not:

- Import AKWB internal modules.
- Instantiate AKWB classes.
- Call AKWB private functions.
- Rely on undocumented file names or formats.
- Write to `.akwb/` unless through AKWB or an explicit extension contract.
- Assume `.akwb/` exists on every developer machine (it may be gitignored).

---

## 3. Supported Artifact Types

The following artifact categories are part of the downstream contract.

| Category | Example Paths | Formats |
|---|---|---|
| **Workspace manifest** | `.akwb/workspace.json` | JSON |
| **Source catalog** | `.akwb/index/source_catalog.jsonl` | JSONL |
| **File fingerprints** | `.akwb/index/file_fingerprints.json` | JSON |
| **Knowledge objects** | `.akwb/knowledge/graph_nodes.jsonl` | JSONL |
| **Knowledge relationships** | `.akwb/knowledge/graph_edges.jsonl` | JSONL |
| **Knowledge catalog** | `.akwb/knowledge/catalog.json` | JSON |
| **Graph export** | `.akwb/graph/graph.jsonl` | JSONL |
| **Graph visualization** | `.akwb/graph/graph.dot` | DOT |
| **Graph query** | `.akwb/graph/graph.cypher` | Cypher |
| **Reports** | `.akwb/reports/*.md`, `.akwb/reports/*.json` | Markdown, JSON |
| **Configuration snapshot** | `.akwb/config/` | YAML/JSON |
| **Logs** | `.akwb/logs/*.log` | Text |

The exact file names and schema versions are documented in `docs/11_DATA_MODEL.md`
and in the schema files themselves. AKWB may add new artifact files; downstream
products must ignore artifacts they do not understand.

---

## 4. Schema Versioning

Every artifact schema is versioned independently of the AKWB engine version.

- Artifact files contain a `schema_version` field where applicable.
- The workspace manifest contains a `schema_version` for the workspace format.
- Plugin API versions are independent of artifact schema versions.

Downstream products should:

- Read the `schema_version` before parsing.
- Ignore fields they do not understand.
- Reject or warn on major version mismatches.

AKWB will not break an existing schema without a migration path and a new
schema version.

---

## 5. Backwards Compatibility Promise

Within a major AKWB version:

- Existing artifact schemas remain readable.
- New fields are additive.
- Existing fields keep their meaning.
- CLI exit codes and output formats remain stable.

Breaking changes require a new major version and a documented migration guide.

Downstream products should target the current stable schema version and plan
for migration when a new major version is announced.

---

## 6. Non-Guarantees

AKWB does not guarantee:

- The presence of a specific artifact if the analysis did not produce it.
- The order of lines in JSONL files.
- The exact set of knowledge types or relationship types across versions.
- The inclusion of AI-generated summaries, embeddings, or RAG context.
- The availability of network, cloud, or SaaS features.

Downstream products must handle missing artifacts gracefully.

---

## 7. What Downstream Products Own

Downstream products are responsible for:

- Rendering UI, dashboards, and visualizations.
- Building chat, agent, and conversational experiences.
- Generating embeddings and vector indexes.
- Managing prompts and prompt versions.
- Publishing branded documents and sites.
- Implementing business logic, workflows, and approvals.
- Integrating with CRM, HRMS, and other business systems.
- Hosting, scaling, billing, and multi-tenant operations.
- Cloud synchronization and federation.

AKWB provides the raw material. Downstream products provide the experience.

---

## 8. Extension Model

Downstream products may extend AKWB through the plugin framework. Plugins must:

- Implement a published port.
- Declare required permissions.
- Not depend on AKWB internals.
- Be placed in a directory configured in `akwb.yaml` or passed to the CLI.

Downstream products must not patch AKWB core code or rely on monkey-patching.

---

## 9. Stability Expectations

AKWB releases follow semantic versioning:

- **Patch releases** fix bugs without changing schemas or contracts.
- **Minor releases** add features, artifact fields, or plugin ports in a
  backwards-compatible way.
- **Major releases** may change schemas, plugin APIs, or CLI contracts with a
  migration guide.

Downstream products should pin AKWB to a major version in CI and test against
new minor versions before upgrading major versions.

---

## 10. Migration Philosophy

AKWB migrates data forward. Downstream products are expected to consume the
current schema.

When a schema changes:

- The old schema is deprecated.
- A migration tool or compatibility reader is provided for one major version.
- After the deprecation window, old schema support is removed.

Downstream products should not depend on legacy schemas indefinitely.

---

## 11. Support and Issue Reporting

Downstream products should report issues related to:

- Artifact schema correctness.
- CLI output correctness.
- Plugin port behavior.
- Workspace corruption or inconsistency.

Issues related to downstream UI, AI behavior, business logic, or cloud
operations are out of scope for AKWB.

---

## 12. Summary

Downstream products integrate with AKWB by reading the `.akwb/` workspace. The
workspace is the only contract. Internal classes, functions, and modules are
not a contract. Schemas are versioned and evolve carefully. Downstream products
own the user experience, business logic, AI behavior, and cloud operations.

If a downstream product finds itself needing AKWB internals, the correct
solution is to request a new artifact, a new export format, or a new plugin port
—not to import engine code.
