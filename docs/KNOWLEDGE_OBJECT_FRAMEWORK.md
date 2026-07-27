# Enterprise Knowledge Object Framework

## Purpose

The `akwb.knowledge` package is the canonical data model for all project knowledge in AKWB. It provides a language-, framework-, and format-agnostic way to represent knowledge objects, their relationships, evidence, confidence, lifecycle, and versioning.

Every parser, AI extractor, knowledge graph builder, memory builder, report generator, and exporter must operate on these primitives or their derivatives.

## Core Abstractions

| Class | Responsibility |
|---|---|
| `KnowledgeObject` | The canonical unit of project knowledge. |
| `KnowledgeType` | Plugin-contributable definition of a class of knowledge objects. |
| `KnowledgeSource` | A source from which a knowledge object was derived (file, conversation, image, AI model, etc.). |
| `KnowledgeReference` | A portable pointer to another knowledge object or external source. |
| `KnowledgeEvidence` | Evidence linking a knowledge claim to a source, location, and confidence. |
| `KnowledgeRelationship` | A typed relationship between two knowledge references. |
| `KnowledgeMetadata` | Contextual metadata (timestamps, tags, domain, custom fields). |
| `KnowledgeVersion` | Versioning metadata (state, previous version, superseded by, timestamps). |
| `KnowledgeConfidence` | A normalized confidence score with method and rationale. |
| `KnowledgeLifecycle` | State machine for lifecycle transitions. |
| `KnowledgeCatalog` | Aggregate of objects, relationships, and type definitions. |
| `KnowledgeFramework` | Central orchestrator loading built-ins, plugins, validators, and serializers. |

## Built-in Knowledge Types

The framework ships with a default set of types covering common enterprise concerns:

- `decision`, `requirement`, `risk`, `issue`, `task`
- `timeline_event`, `business_rule`, `policy`
- `architecture_element`, `technology`, `component`, `capability`, `process`
- `goal`, `objective`, `stakeholder`, `entity`, `glossary_term`
- `question`, `answer`, `prompt`
- `meeting`, `conversation`, `research_finding`
- `metric`, `constraint`, `assumption`, `dependency`, `action_item`
- `document`, `media`

New types can be registered by plugins without modifying core code.

## Built-in Relationship Types

Generic relationship types are provided as defaults:

`depends_on`, `implements`, `supersedes`, `derived_from`, `references`, `contains`, `belongs_to`, `mitigates`, `supports`, `generated_from`, `related_to`.

Plugins may add relationship types and optional type constraints.

## Evidence and Traceability

Every `KnowledgeObject` carries:

- `sources`: a list of `KnowledgeSource`s describing origins.
- `evidence`: a list of `KnowledgeEvidence` records, each pointing to a source, an optional location, an optional excerpt, a confidence, and an extraction provenance.

Traceability is enforced by the `TraceabilityValidator` and the `EvidenceValidator`.

## Versioning and Lifecycle

`KnowledgeVersion` records the current lifecycle state (`draft`, `published`, `updated`, `superseded`, `archived`), version identifier, previous version, and superseded-by reference.

`KnowledgeLifecycle` enforces allowed transitions:

- `draft` → `published`
- `published` → `updated`, `superseded`, `archived`
- `updated` → `published`, `superseded`, `archived`
- `superseded` → `archived`

## Serialization

Three serializers are implemented:

- `JsonSerializer`
- `JsonlSerializer` (line-delimited, each record tagged by kind)
- `YamlSerializer`

All are replaceable through the `KnowledgeSerializer` port.

## Validation

The `KnowledgeFramework` runs registered validators:

- `TypeValidator`: type is registered; optional content schema is respected.
- `RelationshipValidator`: relationship type is registered; endpoints exist; type constraints hold.
- `EvidenceValidator`: evidence sources and types are valid; confidence is in range.
- `TraceabilityValidator`: objects have at least one source or evidence record.
- `MetadataValidator`: required metadata fields and tags are valid.
- `ConfidenceValidator`: confidence values are in [0.0, 1.0].
- `LifecycleValidator`: lifecycle and version states are consistent.

Plugins may contribute additional validators via the `KnowledgeValidatorProvider` port.

## Plugin Extensibility

The framework exposes four plugin ports:

- `KnowledgeTypeProvider`
- `RelationshipTypeProvider`
- `EvidenceTypeProvider`
- `KnowledgeValidatorProvider`

Plugins register through the existing `PluginRegistry` mechanism, and `KnowledgeFramework.load_plugins()` pulls contributions into the framework's registries.

## Usage Example

```python
from akwb.knowledge import KnowledgeFramework
from akwb.knowledge.models import (
    KnowledgeCatalog,
    KnowledgeEvidence,
    KnowledgeObject,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeSource,
)

framework = KnowledgeFramework()
catalog = framework.new_catalog(project="akwb")

source = KnowledgeSource(kind="markdown", uri="docs/adr/001.md")
evid = KnowledgeEvidence(source=source, type="citation", excerpt="We will use PostgreSQL.")

decision = KnowledgeObject(
    type="decision",
    title="Use PostgreSQL",
    sources=[source],
    evidence=[evid],
)
catalog.add_object(decision)

task = KnowledgeObject(
    type="task",
    title="Create database schema",
    sources=[source],
    evidence=[evid],
)
catalog.add_object(task)

rel = KnowledgeRelationship(
    relationship_type="contains",
    from_ref=KnowledgeReference(ref=decision.id),
    to_ref=KnowledgeReference(ref=task.id),
)
catalog.add_relationship(rel)

result = framework.validate_catalog(catalog)
assert result.ok

json_output = framework.serialize_catalog(catalog, fmt="json")
print(json_output)
```

## Module Structure

```
src/akwb/knowledge/
  __init__.py           # Public API
  models.py             # Domain models
  builtins.py           # Built-in types, relationships, evidence types, source kinds
  registries.py         # Generic registries
  validation.py         # Validators and validation results
  serialization.py      # JSON, JSONL, YAML serializers
  plugins.py            # Plugin extension ports
  framework.py          # KnowledgeFramework orchestrator
```

## Dependencies

- `pydantic` for domain model validation and serialization.
- `pyyaml` for YAML serialization.
- Standard `abc`, `enum`, `dataclasses`, and `collections`.

## Future Work

- JSON Schema validation for `content_schema` beyond required fields and primitive types.
- Indexing and graph persistence for `KnowledgeCatalog` (handled by the Knowledge Graph Engine in a later sprint).
- Streaming JSONL readers for very large catalogs.
- Query DSL for selecting objects and relationships.
