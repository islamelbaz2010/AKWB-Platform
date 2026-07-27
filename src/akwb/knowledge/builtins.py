"""Built-in knowledge types, relationship types, evidence types, and source kinds.

These are defaults loaded into every ``KnowledgeFramework``.  Plugins may extend or
override them through the registry without modifying core code.
"""

from __future__ import annotations

from akwb.knowledge.models import (
    EvidenceType,
    KnowledgeType,
    RelationshipType,
)

BUILTIN_SOURCE_KINDS: tuple[str, ...] = (
    "markdown",
    "docx",
    "pdf",
    "html",
    "chatgpt",
    "claude",
    "gemini",
    "code",
    "email",
    "image",
    "audio",
    "video",
    "spreadsheet",
    "database",
    "manual",
    "unknown",
)

BUILTIN_EVIDENCE_TYPES: tuple[EvidenceType, ...] = (
    EvidenceType(id="citation", name="Citation"),
    EvidenceType(id="quotation", name="Quotation"),
    EvidenceType(id="summary", name="Summary"),
    EvidenceType(id="derivation", name="Derivation"),
    EvidenceType(id="annotation", name="Annotation"),
    EvidenceType(id="manual", name="Manual Entry"),
    EvidenceType(id="extraction", name="Extraction"),
    EvidenceType(id="ai_extraction", name="AI Extraction"),
    EvidenceType(id="inferred", name="Inferred"),
)

BUILTIN_RELATIONSHIP_TYPES: tuple[RelationshipType, ...] = (
    RelationshipType(id="depends_on", name="Depends On", directed=True),
    RelationshipType(id="implements", name="Implements", directed=True),
    RelationshipType(id="supersedes", name="Supersedes", directed=True),
    RelationshipType(id="derived_from", name="Derived From", directed=True),
    RelationshipType(id="references", name="References", directed=True),
    RelationshipType(id="contains", name="Contains", directed=True),
    RelationshipType(id="belongs_to", name="Belongs To", directed=True),
    RelationshipType(id="mitigates", name="Mitigates", directed=True),
    RelationshipType(id="supports", name="Supports", directed=True),
    RelationshipType(id="generated_from", name="Generated From", directed=True),
    RelationshipType(id="related_to", name="Related To", directed=False),
)

BUILTIN_TYPES: tuple[KnowledgeType, ...] = (
    KnowledgeType(id="decision", name="Decision", category="governance"),
    KnowledgeType(id="requirement", name="Requirement", category="domain"),
    KnowledgeType(id="risk", name="Risk", category="governance"),
    KnowledgeType(id="issue", name="Issue", category="governance"),
    KnowledgeType(id="task", name="Task", category="execution"),
    KnowledgeType(id="timeline_event", name="Timeline Event", category="execution"),
    KnowledgeType(id="business_rule", name="Business Rule", category="domain"),
    KnowledgeType(id="policy", name="Policy", category="governance"),
    KnowledgeType(id="architecture_element", name="Architecture Element", category="engineering"),
    KnowledgeType(id="technology", name="Technology", category="engineering"),
    KnowledgeType(id="component", name="Component", category="engineering"),
    KnowledgeType(id="capability", name="Capability", category="domain"),
    KnowledgeType(id="process", name="Process", category="domain"),
    KnowledgeType(id="goal", name="Goal", category="strategic"),
    KnowledgeType(id="objective", name="Objective", category="strategic"),
    KnowledgeType(id="stakeholder", name="Stakeholder", category="domain"),
    KnowledgeType(id="entity", name="Entity", category="domain"),
    KnowledgeType(id="glossary_term", name="Glossary Term", category="domain"),
    KnowledgeType(id="question", name="Question", category="evidence"),
    KnowledgeType(id="answer", name="Answer", category="evidence"),
    KnowledgeType(id="prompt", name="Prompt", category="ai"),
    KnowledgeType(id="meeting", name="Meeting", category="communication"),
    KnowledgeType(id="conversation", name="Conversation", category="communication"),
    KnowledgeType(id="research_finding", name="Research Finding", category="evidence"),
    KnowledgeType(id="metric", name="Metric", category="execution"),
    KnowledgeType(id="constraint", name="Constraint", category="domain"),
    KnowledgeType(id="assumption", name="Assumption", category="domain"),
    KnowledgeType(id="dependency", name="Dependency", category="engineering"),
    KnowledgeType(id="action_item", name="Action Item", category="execution"),
    KnowledgeType(id="document", name="Document", category="media"),
    KnowledgeType(id="media", name="Media", category="media"),
)
