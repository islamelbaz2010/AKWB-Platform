"""Tests for the extraction pipeline orchestration."""

from akwb.domain.models import Artifact
from akwb.extraction.pipeline import ExtractionPipeline


def test_pipeline_extracts_text_artifact() -> None:
    pipeline = ExtractionPipeline()
    artifact = Artifact(
        name="adr.md",
        relative_path="docs/adr.md",
        mime_type="text/markdown",
    )
    text = "# Decision to use Postgres\n\nWe will use PostgreSQL for the data store."
    result = pipeline.extract(artifact, text, project_id="akwb")

    assert result.ok
    assert result.candidate_count >= 1
    assert len(result.objects) >= 1
    titles = {obj.title for obj in result.objects}
    assert "Decision to use Postgres" in titles
    assert all(obj.sources for obj in result.objects)
    assert all(obj.evidence for obj in result.objects)


def test_pipeline_extracts_structured_json() -> None:
    pipeline = ExtractionPipeline()
    artifact = Artifact(
        name="data.json",
        relative_path="data.json",
        mime_type="application/json",
    )
    data = '{"decision": "Use Postgres", "owner": "team"}'
    result = pipeline.extract(artifact, data)

    assert result.ok
    assert result.candidate_count >= 1
    assert len(result.objects) >= 1
    assert any(obj.type == "entity" for obj in result.objects)


def test_pipeline_rejects_unknown_mime_type() -> None:
    pipeline = ExtractionPipeline()
    artifact = Artifact(
        name="doc.unknown",
        relative_path="doc.unknown",
        mime_type="application/x-unknown",
    )
    result = pipeline.extract(artifact, b"data")
    assert not result.ok
    assert any("No reader" in d.message for d in result.diagnostics)


def test_pipeline_extracts_code_and_table() -> None:
    pipeline = ExtractionPipeline()
    artifact = Artifact(
        name="spec.md",
        relative_path="spec.md",
        mime_type="text/markdown",
    )
    text = (
        "# Task implementation\n\n"
        "```python\n"
        "def run(): pass\n"
        "```\n\n"
        "| Step | Done |\n"
        "|------|------|\n"
        "| 1    | yes  |\n"
    )
    result = pipeline.extract(artifact, text)

    assert result.ok
    types = {obj.type for obj in result.objects}
    assert "component" in types or "business_rule" in types or "task" in types
