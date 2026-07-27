"""Dependency injection composition root for AKWB."""

from __future__ import annotations

from pathlib import Path

from akwb.config import Config, ConfigLoader
from akwb.discovery.engine import DiscoveryEngine
from akwb.events import InMemoryEventBus
from akwb.extraction.pipeline import ExtractionPipeline
from akwb.graph.engine import GraphEngine
from akwb.graph.storage import LocalGraphStorage
from akwb.knowledge.framework import KnowledgeFramework
from akwb.observability import LoggerObservability
from akwb.plugins.loader import PluginLoader
from akwb.plugins.registry import PluginRegistry
from akwb.storage import LocalStorageBackend, UnitOfWork
from akwb.workspace import WorkspaceBootstrap


class Container:
    """Wire together the core services for a single AKWB invocation."""

    def __init__(self, project_root: Path, config: Config | None = None) -> None:
        self.project_root = project_root.resolve()
        self.config = config or ConfigLoader().load(self.project_root)
        self.observability = LoggerObservability(level=self.config.log_level)
        self.event_bus = InMemoryEventBus()

        workspace_path = self.project_root / self.config.workspace_dir
        self.storage = LocalStorageBackend(
            workspace_path,
            event_bus=self.event_bus,
        )
        self.unit_of_work = UnitOfWork(self.storage)

        self.plugin_loader = PluginLoader()
        self.plugin_registry = PluginRegistry(
            loader=self.plugin_loader,
            observability=self.observability,
        )

        self.workspace_bootstrap = WorkspaceBootstrap(
            self.config,
            self.storage,
            self.event_bus,
            self.observability,
        )

        self.discovery_engine = DiscoveryEngine(
            self.config,
            self.storage,
            self.event_bus,
            self.observability,
        )

        self.knowledge_framework = KnowledgeFramework(
            observability=self.observability,
        )
        self.extraction_pipeline = ExtractionPipeline(
            framework=self.knowledge_framework,
            observability=self.observability,
        )
        self.graph_engine = GraphEngine(
            framework=self.knowledge_framework,
        )

    def load_plugins(self) -> None:
        """Load all configured plugin directories and extend engines."""
        self.plugin_registry.load_all(self.config.plugins.directories)
        self.knowledge_framework.load_plugins(self.plugin_registry)
        self.extraction_pipeline.load_plugins(self.plugin_registry)
        self.graph_engine.load_plugins(self.plugin_registry)
        if self.graph_engine.storage is None:
            self.graph_engine.storage = LocalGraphStorage(self.storage)
