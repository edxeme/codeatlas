"""Command-line interface for codeatlas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codeatlas.graph import build_graph
from codeatlas.scanner import ProjectReport, scan_tree


def _print_scan(report: ProjectReport) -> None:
    header = f"{'module':<44} {'loc':>5} {'cls':>4} {'fns':>4} {'cx':>5} {'imp':>4}"
    print(header)
    print("-" * len(header))
    for module in report.modules:
        print(
            f"{module.path:<44} {module.loc:>5} {len(module.classes):>4} "
            f"{len(module.functions):>4} {module.total_complexity:>5} "
            f"{len(module.imports):>4}"
        )
    totals = report.totals
    print("-" * len(header))
    print(
        f"{totals['modules']} modules · {totals['loc']} loc · "
        f"{totals['classes']} classes · {totals['functions']} functions"
    )
    if totals["syntax_errors"]:
        print(
            f"warning: could not parse {totals['syntax_errors']} file(s):",
            file=sys.stderr,
        )
        for module in report.unparsable:
            print(f"  {module.path}: {module.syntax_error}", file=sys.stderr)


def rank_hotspots(report: ProjectReport, top: int) -> list[tuple]:
    """The *top* functions by complexity, then size, then name for determinism."""
    ranked = [
        (function, module)
        for module in report.modules
        for function in module.functions
    ]
    ranked.sort(key=lambda pair: (-pair[0].complexity, -pair[0].loc, pair[0].qualname))
    return ranked[:top]


def _print_hotspots(ranked: list[tuple]) -> None:
    header = f"{'cx':>4}  {'location':<48} {'function'}"
    print(header)
    print("-" * len(header))
    for function, module in ranked:
        location = f"{module.path}:{function.lineno}"
        print(f"{function.complexity:>4}  {location:<48} {function.qualname}")


def _ranked_to_dict(ranked: list[tuple]) -> list[dict]:
    return [
        {
            "complexity": function.complexity,
            "location": f"{module.path}:{function.lineno}",
            "qualname": function.qualname,
        }
        for function, module in ranked
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codeatlas",
        description="Map a Python codebase: inventory, hotspots and import graph.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="inventory every module under PATH")
    p_scan.add_argument("path", help="project root to scan")
    p_scan.add_argument("--json", action="store_true", help="emit the full report as JSON")

    p_hot = sub.add_parser("hotspots", help="rank the most complex functions")
    p_hot.add_argument("path", help="project root to scan")
    p_hot.add_argument(
        "-n", "--top", type=int, default=10, help="how many functions to show"
    )
    p_hot.add_argument("--json", action="store_true", help="emit the ranking as JSON")

    p_graph = sub.add_parser("graph", help="internal import graph as DOT or JSON")
    p_graph.add_argument("path", help="project root to scan")
    p_graph.add_argument("--json", action="store_true", help="emit nodes and edges as JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.is_dir():
        parser.exit(1, f"codeatlas: not a directory: {args.path}\n")

    report = scan_tree(root)
    if args.command == "scan":
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            _print_scan(report)
    elif args.command == "hotspots":
        ranked = rank_hotspots(report, args.top)
        if args.json:
            print(json.dumps(_ranked_to_dict(ranked), indent=2))
        else:
            _print_hotspots(ranked)
    elif args.command == "graph":
        graph = build_graph(report)
        if args.json:
            print(json.dumps(graph.to_dict(), indent=2))
        else:
            print(graph.to_dot())
    return 0
