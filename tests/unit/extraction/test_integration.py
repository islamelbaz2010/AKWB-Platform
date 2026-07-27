"""Integration tests for the extraction pipeline with plugins."""

from pathlib import Path

import pytest

from akwb.domain.models import Artifact
from akwb.extraction.models import ContentKind, NormalizedContent
from akwb.extraction.pipeline import ExtractionPipeline
from akwb.extraction.plugins import Reader
from akwb.plugins.registry import PluginRegistry


@pytest.fixture
def extraction_plugin_dir() -> Path:
    return Path(__file__).parent.parent.parent / "fixtures" / "extraction_plugin"


class PrefixStripReader(Reader):
    """Plugin reader that strips a known prefix before normalization."""

    supported_mime_types = ("text/x-custom",)

    def read(self, artifact, content, context=None):
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        return NormalizedContent(
            kind=ContentKind.TEXT,
            mime_type=artifact.mime_type,
            content=text.removeprefix(".CUSTOM "),
            source_uri=artifact.relative_path or artifact.name,
        )


def test_pipeline_uses_plugin_reader(extraction_plugin_dir: Path) -> None:
    plugin_registry = PluginRegistry()
    result = plugin_registry.load_from_directory(extraction_plugin_dir)
    assert result.ok, result.error

    pipeline = ExtractionPipeline()
    pipeline.load_plugins(plugin_registry)

    artifact = Artifact(
        name="custom.txt",
        relative_path="custom.txt",
        mime_type="text/x-custom",
    )
    result = pipeline.extract(artifact, ".CUSTOM # Decision\n\nUse Postgres.")

    assert result.ok
    assert any(obj.title == "Decision" for obj in result.objects)


def test_manual_plugin_reader() -> None:
    pipeline = ExtractionPipeline()
    pipeline.register_reader(PrefixStripReader())

    artifact = Artifact(
        name="custom.txt",
        relative_path="custom.txt",
        mime_type="text/x-custom",
    )
    result = pipeline.extract(artifact, ".CUSTOM # Decision\n\nUse Postgres.")
    assert result.ok
    assert any(obj.title == "Decision" for obj in result.objects)
