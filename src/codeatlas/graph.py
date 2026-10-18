"""Internal import graph between the scanned modules.

Resolution is heuristic and path-based:

- Relative imports (``from .scanner import ...``) resolve against the
  importing file's own directory, walking up one level per extra dot.
- Absolute imports match a module's dotted name, derived from its path
  relative to the scan root; ``src/`` prefixes are trimmed so both flat
  and src-layout trees resolve.

Anything that cannot be matched inside the tree — the standard library,
third-party packages — is external and dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from codeatlas.scanner import ProjectReport


def display_name(rel_path: str) -> str:
    """Dotted module name for display: ``src/x/cli.py`` -> ``x.cli``."""
    parts = list(PurePosixPath(rel_path).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if parts and parts[0] in ("src", "lib"):
        parts = parts[1:]
    return ".".join(parts) if parts else "."


def _relative_target(module_path: str, imp: str, known: set[str]) -> str | None:
    """Resolve a relative import to a file in the scan, if it lands on one."""
    level = len(imp) - len(imp.lstrip("."))
    if not level:
        return None

    rest = imp[level:]
    base = list(PurePosixPath(module_path).parts[:-1])
    hops = level - 1
    if hops > len(base):
        return None
    target_dir = base[: len(base) - hops] if hops else base
    target_dir = target_dir + rest.split(".") if rest else target_dir

    joined = "/".join(target_dir)
    for candidate in (f"{joined}.py", f"{joined}/__init__.py"):
        if candidate in known:
            return candidate
    return None


def _absolute_target(imp: str, by_key: dict[str, str]) -> str | None:
    """Resolve an absolute import against dotted names seen in the scan."""
    if imp in by_key:
        return by_key[imp]
    matches = [path for key, path in by_key.items() if key.startswith(imp + ".")]
    return min(matches, key=len) if matches else None


@dataclass
class ImportGraph:
    """Nodes as dotted display names, edges as (importer, imported) pairs."""

    nodes: list[str]
    edges: list[tuple[str, str]]

    def to_dot(self) -> str:
        """Graphviz DOT rendering, left-to-right."""
        lines = ["digraph codeatlas {", "  rankdir=LR;"]
        lines.extend(f'  "{src}" -> "{dst}";' for src, dst in self.edges)
        lines.append("}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """JSON-friendly representation."""
        return {"nodes": self.nodes, "edges": [list(edge) for edge in self.edges]}


def build_graph(report: ProjectReport) -> ImportGraph:
    """Resolve every recorded import that lands inside the scanned tree."""
    parsable = [m for m in report.modules if m.syntax_error is None]
    by_path = {m.path for m in parsable}

    by_key: dict[str, str] = {}
    for module in parsable:
        parts = list(PurePosixPath(module.path).with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        by_key.setdefault(".".join(parts), module.path)
        if len(parts) > 1 and parts[0] in ("src", "lib"):
            by_key.setdefault(".".join(parts[1:]), module.path)

    edges: set[tuple[str, str]] = set()
    for module in parsable:
        for imp in module.imports:
            target = _relative_target(module.path, imp, by_path) or _absolute_target(imp, by_key)
            if target and target != module.path:
                edges.add((display_name(module.path), display_name(target)))

    nodes = sorted({display_name(m.path) for m in parsable})
    return ImportGraph(nodes=nodes, edges=sorted(edges))
