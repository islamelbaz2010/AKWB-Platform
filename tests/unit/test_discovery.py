"""Tests for the Discovery Foundation components."""

import os
from pathlib import Path

import pytest

from akwb.config import Config
from akwb.discovery.classifier import FileClassifier
from akwb.discovery.engine import DiscoveryEngine
from akwb.discovery.fingerprint import FingerprintEngine
from akwb.discovery.ignore import IgnoreEngine
from akwb.discovery.incremental import IncrementalDetector
from akwb.discovery.models import ArtifactEntry, ArtifactRegistry
from akwb.discovery.scanner import RecursiveScanner
from akwb.events import InMemoryEventBus
from akwb.observability import LoggerObservability
from akwb.storage import LocalStorageBackend


def _build_engine(project_root: Path) -> DiscoveryEngine:
    config = Config()
    bus = InMemoryEventBus()
    obs = LoggerObservability(level="ERROR")
    storage = LocalStorageBackend(project_root / config.workspace_dir, event_bus=bus)
    return DiscoveryEngine(config, storage, bus, obs)


def test_ignore_engine_default_patterns(temp_project: Path) -> None:
    ignore = IgnoreEngine(temp_project, ["node_modules", ".git"])
    (temp_project / ".git" / "config").parent.mkdir(parents=True)
    (temp_project / ".git" / "config").write_text("x")
    (temp_project / "src" / "main.py").parent.mkdir(parents=True)
    (temp_project / "src" / "main.py").write_text("x")

    assert ignore.is_ignored(temp_project / ".git" / "config") is True
    assert ignore.is_ignored(temp_project / "src" / "main.py") is False


def test_ignore_engine_project_akwbignore(temp_project: Path) -> None:
    (temp_project / ".akwbignore").write_text("*.log\n")
    (temp_project / "debug.log").write_text("x")
    (temp_project / "app.txt").write_text("x")

    ignore = IgnoreEngine(temp_project, [])
    assert ignore.is_ignored(temp_project / "debug.log") is True
    assert ignore.is_ignored(temp_project / "app.txt") is False


def test_classifier_known_extensions() -> None:
    cls = FileClassifier()
    assert cls.classify(Path("x.py")) == ("source_code", "code")
    assert cls.classify(Path("x.md")) == ("markdown", "document")
    assert cls.classify(Path("x.json")) == ("json", "data")
    assert cls.classify(Path("x.png")) == ("image", "media")
    assert cls.classify(Path("x.zip")) == ("archive", "archive")


def test_classifier_directory() -> None:
    cls = FileClassifier()
    assert cls.classify(Path("somedir"), is_directory=True) == ("directory", "directory")


def test_fingerprint_stable_id_deterministic() -> None:
    fp = FingerprintEngine()
    assert fp.stable_id("src/main.py") == fp.stable_id("src/main.py")
    assert fp.stable_id("src/main.py") != fp.stable_id("src/other.py")


def test_fingerprint_hash_file(temp_project: Path) -> None:
    fp = FingerprintEngine()
    file_path = temp_project / "hello.txt"
    file_path.write_text("hello")
    assert fp.hash_file(file_path) is not None
    assert len(fp.hash_file(file_path)) == 64  # sha256 hex length


def test_recursive_scanner(temp_project: Path) -> None:
    (temp_project / ".git" / "config").parent.mkdir(parents=True)
    (temp_project / ".git" / "config").write_text("x")
    (temp_project / "src" / "main.py").parent.mkdir(parents=True)
    (temp_project / "src" / "main.py").write_text("x")

    ignore = IgnoreEngine(temp_project, [".git"])
    scanner = RecursiveScanner(ignore)
    items = list(scanner.scan(temp_project))
    relative_paths = {i.relative_path for i in items}
    assert "src" in relative_paths
    assert "src/main.py" in relative_paths
    assert ".git/config" not in relative_paths


def test_recursive_scanner_symlinks_not_followed(temp_project: Path) -> None:
    source = temp_project / "a.txt"
    source.write_text("data")
    link = temp_project / "link_to_a"
    link.symlink_to(source)

    ignore = IgnoreEngine(temp_project, [])
    scanner = RecursiveScanner(ignore, follow_symlinks=False)
    items = list(scanner.scan(temp_project))
    assert all(i.relative_path != "link_to_a" for i in items)


def test_incremental_detector_new_and_modified(temp_project: Path) -> None:
    fp = FingerprintEngine()
    prev = ArtifactRegistry(project_root=str(temp_project))
    prev.add(
        ArtifactEntry(
            id=fp.stable_id("old.txt"),
            absolute_path=str(temp_project / "old.txt"),
            relative_path="old.txt",
            type="text",
            category="document",
            extension="txt",
            hash=fp.hash_file(temp_project / "old.txt"),
            size=0,
            created_time="2024-01-01T00:00:00+00:00",
            modified_time="2024-01-01T00:00:00+00:00",
            parent_directory=str(temp_project),
        )
    )

    (temp_project / "new.txt").write_text("new content")
    curr = ArtifactRegistry(project_root=str(temp_project))
    curr.add(
        ArtifactEntry(
            id=fp.stable_id("new.txt"),
            absolute_path=str(temp_project / "new.txt"),
            relative_path="new.txt",
            type="text",
            category="document",
            extension="txt",
            hash=fp.hash_file(temp_project / "new.txt"),
            size=0,
            created_time="2024-01-01T00:00:00+00:00",
            modified_time="2024-01-01T00:00:00+00:00",
            parent_directory=str(temp_project),
        )
    )

    detector = IncrementalDetector()
    changes = detector.detect(prev, curr)
    assert len(changes.added) == 1
    assert changes.added[0].relative_path == "new.txt"
    assert len(changes.deleted) == 1
    assert changes.deleted[0].relative_path == "old.txt"


def test_discovery_engine_ignores_and_classifies(temp_project: Path) -> None:
    (temp_project / "src" / "main.py").parent.mkdir(parents=True)
    (temp_project / "src" / "main.py").write_text("print(1)")
    (temp_project / "README.md").write_text("# project")
    (temp_project / "node_modules" / "pkg" / "index.js").parent.mkdir(parents=True)
    (temp_project / "node_modules" / "pkg" / "index.js").write_text("x")
    (temp_project / "app.log").write_text("log")
    (temp_project / ".akwbignore").write_text("*.log\n")

    engine = _build_engine(temp_project)
    result = engine.discover(temp_project)
    assert result.ok is True
    registry = result.value
    relative_paths = {a.relative_path for a in registry.all()}
    assert "README.md" in relative_paths
    assert "src/main.py" in relative_paths
    assert "app.log" not in relative_paths
    assert "node_modules/pkg/index.js" not in relative_paths

    py = registry.by_path("src/main.py")
    assert py is not None
    assert py.type == "source_code"
    assert py.category == "code"


def test_discovery_registry_persistence(temp_project: Path) -> None:
    (temp_project / "file.txt").write_text("data")

    engine = _build_engine(temp_project)
    engine.discover(temp_project)

    assert (temp_project / ".akwb" / "artifacts.json").exists()

    loaded = ArtifactRegistry.load(engine._storage)
    assert loaded.by_path("file.txt") is not None
    assert len(loaded.all()) == 1


def test_discovery_empty_project(temp_project: Path) -> None:
    engine = _build_engine(temp_project)
    result = engine.discover(temp_project)
    assert result.ok is True
    assert len(result.value.all()) == 0


def test_discovery_nested_folders(temp_project: Path) -> None:
    (temp_project / "a" / "b" / "c" / "deep.txt").parent.mkdir(parents=True)
    (temp_project / "a" / "b" / "c" / "deep.txt").write_text("deep")

    engine = _build_engine(temp_project)
    result = engine.discover(temp_project)
    assert result.ok is True
    paths = {a.relative_path for a in result.value.all()}
    assert "a/b/c/deep.txt" in paths
    assert "a" in paths
    assert "a/b" in paths
    assert "a/b/c" in paths


def test_discovery_large_project(temp_project: Path) -> None:
    for i in range(100):
        (temp_project / f"file_{i:03d}.txt").write_text(f"content {i}")

    engine = _build_engine(temp_project)
    result = engine.discover(temp_project)
    assert result.ok is True
    assert len(result.value.all()) == 100


def test_discovery_duplicate_files(temp_project: Path) -> None:
    (temp_project / "a.txt").write_text("same content")
    (temp_project / "b.txt").write_text("same content")

    engine = _build_engine(temp_project)
    result = engine.discover(temp_project)
    assert result.ok is True
    assert len(result.value.all()) == 2
    entries = sorted(result.value.all(), key=lambda a: a.relative_path)
    assert entries[0].id != entries[1].id  # unique IDs
    assert entries[0].hash == entries[1].hash  # same content hash


def test_discovery_modified_file(temp_project: Path) -> None:
    target = temp_project / "mutable.txt"
    target.write_text("original")

    engine = _build_engine(temp_project)
    engine.discover(temp_project)

    target.write_text("changed")
    result = engine.discover(temp_project)
    assert result.ok is True

    entry = result.value.by_path("mutable.txt")
    assert entry is not None
    assert entry.status == "modified"


def test_discovery_renamed_file(temp_project: Path) -> None:
    source = temp_project / "old_name.txt"
    source.write_text("stable content")

    engine = _build_engine(temp_project)
    engine.discover(temp_project)

    dest = temp_project / "new_name.txt"
    source.rename(dest)
    result = engine.discover(temp_project)
    assert result.ok is True

    entry = result.value.by_path("new_name.txt")
    assert entry is not None
    assert entry.status == "renamed"
    assert entry.previous_path == "old_name.txt"


def test_discovery_deleted_file(temp_project: Path) -> None:
    target = temp_project / "remove_me.txt"
    target.write_text("temporary")

    engine = _build_engine(temp_project)
    engine.discover(temp_project)

    target.unlink()
    result = engine.discover(temp_project)
    assert result.ok is True

    assert result.value.by_path("remove_me.txt") is None


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks not supported")
def test_scanner_follow_symlinks(temp_project: Path) -> None:
    import os

    real_dir = temp_project / "real"
    real_dir.mkdir()
    (real_dir / "inside.txt").write_text("inside")
    link_dir = temp_project / "link"
    os.symlink(real_dir, link_dir)

    ignore = IgnoreEngine(temp_project, [])
    scanner = RecursiveScanner(ignore, follow_symlinks=True, include_directories=False)
    items = list(scanner.scan(temp_project))
    paths = {i.relative_path for i in items}
    assert "link/inside.txt" in paths


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks not supported")
def test_scanner_skip_symlink_files(temp_project: Path) -> None:
    import os

    real = temp_project / "real.txt"
    real.write_text("data")
    link = temp_project / "link.txt"
    os.symlink(real, link)

    ignore = IgnoreEngine(temp_project, [])
    scanner = RecursiveScanner(ignore, follow_symlinks=False)
    items = list(scanner.scan(temp_project))
    paths = {i.relative_path for i in items}
    assert "link.txt" not in paths
    assert "real.txt" in paths
