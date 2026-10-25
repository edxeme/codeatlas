"""Single-pass AST inventory of a Python project.

Walks every ``*.py`` file under a root directory, parses it once, and
records the modules, classes and functions it finds — each function scored
with its cyclomatic complexity from :mod:`codeatlas.complexity` — plus the
raw import statements for :mod:`codeatlas.graph` to resolve.

Files that cannot be read or parsed are *reported*, never fatal: an
inventory that dies on one broken file is useless on real codebases.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path

from codeatlas.complexity import cyclomatic_complexity

#: Directories that never belong in an inventory (VCS internals, caches,
#: virtualenvs, build outputs).
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", ".nox", ".venv", "venv", "__pycache__", "node_modules",
    "build", "dist", ".eggs", "site-packages",
}


@dataclass
class FunctionInfo:
    """A function or method: location, size and complexity."""

    qualname: str
    lineno: int
    end_lineno: int
    params: int
    loc: int
    complexity: int
    has_docstring: bool


@dataclass
class ClassInfo:
    """A class: location, method count and documentation flag."""

    name: str
    lineno: int
    methods: int
    has_docstring: bool


@dataclass
class ModuleInfo:
    """One ``*.py`` file: size, members, imports and parse status."""

    path: str  # POSIX-style, relative to the scan root
    loc: int = 0
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    syntax_error: str | None = None

    @property
    def total_complexity(self) -> int:
        return sum(f.complexity for f in self.functions)


@dataclass
class ProjectReport:
    """Aggregated result of scanning a root directory."""

    root: str
    modules: list[ModuleInfo] = field(default_factory=list)

    @property
    def unparsable(self) -> list[ModuleInfo]:
        return [m for m in self.modules if m.syntax_error is not None]

    @property
    def totals(self) -> dict[str, int]:
        return {
            "modules": len(self.modules),
            "loc": sum(m.loc for m in self.modules),
            "classes": sum(len(m.classes) for m in self.modules),
            "functions": sum(len(m.functions) for m in self.modules),
            "syntax_errors": len(self.unparsable),
        }

    def to_dict(self) -> dict:
        """JSON-friendly representation (paths as POSIX strings)."""
        return {
            "root": self.root,
            "totals": self.totals,
            "modules": [asdict(m) for m in self.modules],
        }


def iter_python_files(root: Path) -> list[Path]:
    """All ``*.py`` files under *root*, skipping caches, VCS dirs and symlinks."""
    found: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_symlink():
            continue
        if any((root / parent).is_symlink() for parent in rel.parents if parent != Path(".")):
            continue
        found.append(path)
    return sorted(found)


class _ModuleVisitor(ast.NodeVisitor):
    """Collects classes, functions (with qualnames) and imports in one pass."""

    def __init__(self) -> None:
        self.classes: list[ClassInfo] = []
        self.functions: list[FunctionInfo] = []
        self.imports: list[str] = []
        self._scope: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        methods = sum(
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            for child in node.body
        )
        self.classes.append(
            ClassInfo(
                name=node.name,
                lineno=node.lineno,
                methods=methods,
                has_docstring=ast.get_docstring(node) is not None,
            )
        )
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function(node)

    def _function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        params = (
            len(node.args.posonlyargs)
            + len(node.args.args)
            + len(node.args.kwonlyargs)
            + (1 if node.args.vararg else 0)
            + (1 if node.args.kwarg else 0)
        )
        end = node.end_lineno or node.lineno
        self.functions.append(
            FunctionInfo(
                qualname=".".join([*self._scope, node.name]),
                lineno=node.lineno,
                end_lineno=end,
                params=params,
                loc=end - node.lineno + 1,
                complexity=cyclomatic_complexity(node),
                has_docstring=ast.get_docstring(node) is not None,
            )
        )
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.extend(alias.name for alias in node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = "." * node.level + (node.module or "")
        self.imports.append(base)
        if not node.module and node.level:
            # ``from . import mod`` — each alias names a sibling submodule.
            for alias in node.names:
                if alias.name != "*":
                    self.imports.append(f"{base}{alias.name}")
        elif node.level == 0:
            # ``from pkg import mod`` — mod may be a submodule of pkg.
            for alias in node.names:
                if alias.name != "*":
                    self.imports.append(f"{node.module}.{alias.name}")


def scan_file(path: Path, root: Path) -> ModuleInfo:
    """Inventory one file; unreadable or unparsable files are flagged, not raised."""
    module = ModuleInfo(path=path.relative_to(root).as_posix())
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        module.syntax_error = f"unreadable: {exc}"
        return module

    module.loc = len(source.splitlines())
    try:
        tree = ast.parse(source, filename=module.path)
    except (SyntaxError, ValueError, RecursionError) as exc:
        module.syntax_error = f"{type(exc).__name__}: {exc}"
        return module

    visitor = _ModuleVisitor()
    visitor.visit(tree)
    module.classes = visitor.classes
    module.functions = visitor.functions
    seen: set[str] = set()
    module.imports = [i for i in visitor.imports if not (i in seen or seen.add(i))]
    return module


def scan_tree(root: Path | str) -> ProjectReport:
    """Scan every Python file under *root* into a :class:`ProjectReport`."""
    root = Path(root).resolve()
    return ProjectReport(
        root=str(root),
        modules=[scan_file(path, root) for path in iter_python_files(root)],
    )
