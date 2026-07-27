"""Minimal Python source-code parser for the AKWB extraction pipeline.

This parser uses the standard ``ast`` module.  It produces ``component``
knowledge objects for modules (passed in as the parent), classes, functions,
and top-level assignments.  It also records import references so that the
caller can create ``depends_on`` relationships.
"""

from __future__ import annotations

import ast
import contextlib
import dataclasses
from pathlib import Path

from akwb.knowledge.models import (
    KnowledgeConfidence,
    KnowledgeEvidence,
    KnowledgeMetadata,
    KnowledgeObject,
    KnowledgeSource,
)


@dataclasses.dataclass
class PythonParseResult:
    """Output of parsing a single Python source file."""

    objects: list[KnowledgeObject] = dataclasses.field(default_factory=list)
    import_targets: list[str] = dataclasses.field(default_factory=list)


class PythonSourceParser:
    """Parse Python source into knowledge objects and import targets."""

    def __init__(
        self,
        parent: KnowledgeObject,
        source: KnowledgeSource,
        project_root: Path,
        relative_path: str,
    ) -> None:
        self.parent = parent
        self.source = source
        self.project_root = project_root
        self.relative_path = relative_path

    def parse(self, content: str) -> PythonParseResult:
        """Parse ``content`` and return discovered objects and import targets."""
        tree = ast.parse(content, filename=self.relative_path)
        result = PythonParseResult()
        lines = content.splitlines()

        for node in tree.body:
            self._process_top_level_node(node, content, lines, result)

        return result

    def _process_top_level_node(
        self,
        node: ast.AST,
        content: str,
        lines: list[str],
        result: PythonParseResult,
    ) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.objects.append(
                self._function_object(node, content, lines)
            )
            return

        if isinstance(node, ast.ClassDef):
            result.objects.append(
                self._class_object(node, content, lines)
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result.objects.append(
                        self._function_object(child, content, lines, parent_name=node.name)
                    )
            return

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result.objects.append(
                        self._assignment_object(target, node, content, lines)
                    )
            return

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_target = self._resolve_import(node)
            if import_target is not None:
                result.import_targets.append(import_target)

    def _make_source(self, node: ast.AST) -> KnowledgeSource:
        return KnowledgeSource(
            kind="code",
            uri=self.relative_path,
            mime_type=self.source.mime_type,
        )

    def _node_location(self, node: ast.AST) -> str | None:
        if hasattr(node, "lineno"):
            return f"line {node.lineno}"
        return None

    def _make_evidence(
        self,
        node: ast.AST,
        source: KnowledgeSource,
        excerpt: str,
    ) -> KnowledgeEvidence:
        return KnowledgeEvidence(
            source=source,
            type="extraction",
            excerpt=excerpt,
            location=self._node_location(node),
            extracted_by="akwb.extraction.python",
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
        )

    def _function_object(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        content: str,
        lines: list[str],
        parent_name: str | None = None,
    ) -> KnowledgeObject:
        name = node.name
        full_name = f"{parent_name}.{name}" if parent_name else name
        title = f"def {full_name}()" if not parent_name else f"method {full_name}()"
        child_id = self._child_id("func", full_name)

        excerpt = self._node_excerpt(node, content, lines)
        source = self._make_source(node)
        evidence = self._make_evidence(node, source, excerpt)

        return KnowledgeObject(
            id=child_id,
            type="component",
            title=title,
            description=title,
            content=excerpt,
            sources=[source],
            evidence=[evidence],
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
            metadata=KnowledgeMetadata(
                project_id=self.parent.metadata.project_id,
                custom={"language": "python", "name": name, "full_name": full_name},
            ),
        )

    def _class_object(
        self,
        node: ast.ClassDef,
        content: str,
        lines: list[str],
    ) -> KnowledgeObject:
        name = node.name
        child_id = self._child_id("class", name)
        title = f"class {name}"

        excerpt = self._node_excerpt(node, content, lines)
        source = self._make_source(node)
        evidence = self._make_evidence(node, source, excerpt)

        return KnowledgeObject(
            id=child_id,
            type="component",
            title=title,
            description=title,
            content=excerpt,
            sources=[source],
            evidence=[evidence],
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
            metadata=KnowledgeMetadata(
                project_id=self.parent.metadata.project_id,
                custom={"language": "python", "name": name},
            ),
        )

    def _assignment_object(
        self,
        target: ast.Name,
        node: ast.Assign,
        content: str,
        lines: list[str],
    ) -> KnowledgeObject:
        name = target.id
        value_text = self._value_text(node.value)
        title = f"{name} = {value_text}"
        if len(title) > 80:
            title = title[:77] + "..."
        child_id = self._child_id("var", name)

        excerpt = self._node_excerpt(node, content, lines)
        source = self._make_source(node)
        evidence = self._make_evidence(node, source, excerpt)

        return KnowledgeObject(
            id=child_id,
            type="component",
            title=title,
            description=title,
            content=excerpt,
            sources=[source],
            evidence=[evidence],
            confidence=KnowledgeConfidence(value=1.0, method="algorithm"),
            metadata=KnowledgeMetadata(
                project_id=self.parent.metadata.project_id,
                custom={"language": "python", "name": name},
            ),
        )

    def _child_id(self, kind: str, name: str) -> str:
        module_id = self._module_id()
        return f"ku://comp/{module_id}/{kind}/{name}"

    def _module_id(self) -> str:
        return Path(self.relative_path).with_suffix("").as_posix().replace("/", ".")

    def _node_excerpt(
        self,
        node: ast.AST,
        content: str,
        lines: list[str],
    ) -> str:
        with contextlib.suppress(ValueError, TypeError, OSError):
            segment = ast.get_source_segment(content, node)
            if segment:
                return segment.strip()

        start = getattr(node, "lineno", 1) or 1
        end = getattr(node, "end_lineno", start) or start
        return "\n".join(lines[start - 1 : end])

    @staticmethod
    def _value_text(value: ast.AST) -> str:
        try:
            return ast.unparse(value)
        except (ValueError, TypeError):
            return "..."

    def _resolve_import(self, node: ast.Import | ast.ImportFrom) -> str | None:
        """Return the project-relative path of an imported module, if local."""
        if isinstance(node, ast.Import):
            return self._resolve_import_names(node.names, level=0)

        if isinstance(node, ast.ImportFrom):
            return self._resolve_import_names(node.names, level=node.level or 0, module=node.module)

        return None

    def _resolve_import_names(
        self,
        aliases: list[ast.alias],
        level: int,
        module: str | None = None,
    ) -> str | None:
        """Resolve a single local import to a relative path.

        Only one target is returned per import statement.  Multi-name imports
        are reduced to the first local module that can be resolved.
        """
        parts = Path(self.relative_path).parts
        file_dir_parts = parts[:-1]

        if level > 0:
            # Relative import: walk up level-1 directories from the file's directory.
            up = level - 1
            if up > len(file_dir_parts):
                return None
            base_parts = list(file_dir_parts[:-up]) if up > 0 else list(file_dir_parts)
            if module:
                base_parts.extend(module.split("."))
            else:
                # ``from . import name`` imports a module in the same package.
                if not aliases:
                    return None
                base_parts.append(aliases[0].name)
            candidate = "/".join(base_parts) + ".py"
            if (self.project_root / candidate).exists():
                return candidate
            # Also try package __init__.py
            candidate_init = "/".join(base_parts) + "/__init__.py"
            if (self.project_root / candidate_init).exists():
                return candidate_init
            return None

        # Absolute import.
        if module:
            base = module.replace(".", "/")
            candidate = f"{base}.py"
            if (self.project_root / candidate).exists():
                return candidate
            candidate_init = f"{base}/__init__.py"
            if (self.project_root / candidate_init).exists():
                return candidate_init
        else:
            for alias in aliases:
                candidate = f"{alias.name}.py"
                if (self.project_root / candidate).exists():
                    return candidate
        return None
