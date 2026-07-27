"""Tests for extraction readers."""

import json

import yaml

from akwb.domain.models import Artifact
from akwb.extraction.models import ContentKind
from akwb.extraction.readers import BinaryReader, StructuredReader, TextReader


def test_text_reader_reads_bytes() -> None:
    artifact = Artifact(name="doc.txt", relative_path="doc.txt", mime_type="text/plain")
    reader = TextReader()
    result = reader.read(artifact, b"Hello world")
    assert result.kind == ContentKind.TEXT
    assert result.content == "Hello world"
    assert reader.can_read("text/markdown")


def test_text_reader_reads_string() -> None:
    artifact = Artifact(name="doc.md", relative_path="doc.md", mime_type="text/markdown")
    reader = TextReader()
    result = reader.read(artifact, "# Heading")
    assert result.kind == ContentKind.TEXT
    assert result.content == "# Heading"


def test_binary_reader_reads_bytes() -> None:
    artifact = Artifact(name="image.png", relative_path="image.png", mime_type="image/png")
    reader = BinaryReader()
    result = reader.read(artifact, b"\x89PNG")
    assert result.kind == ContentKind.BINARY
    assert result.content == b"\x89PNG"
    assert reader.can_read("audio/wav")


def test_structured_reader_reads_json() -> None:
    artifact = Artifact(
        name="data.json",
        relative_path="data.json",
        mime_type="application/json",
    )
    reader = StructuredReader()
    result = reader.read(artifact, json.dumps({"key": "value"}))
    assert result.kind == ContentKind.STRUCTURED
    assert result.content == {"key": "value"}


def test_structured_reader_reads_yaml() -> None:
    artifact = Artifact(
        name="data.yaml",
        relative_path="data.yaml",
        mime_type="application/x-yaml",
    )
    reader = StructuredReader()
    result = reader.read(artifact, yaml.safe_dump({"list": [1, 2, 3]}))
    assert result.kind == ContentKind.STRUCTURED
    assert result.content == {"list": [1, 2, 3]}
