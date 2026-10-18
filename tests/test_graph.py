"""Import graph tests against the sample project."""

from codeatlas.graph import build_graph
from codeatlas.scanner import scan_tree


def test_relative_import_creates_edge(make_project):
    graph = build_graph(scan_tree(make_project))

    assert ("pkg.util", "pkg.core") in graph.edges


def test_absolute_internal_import_creates_edge(make_project):
    graph = build_graph(scan_tree(make_project))

    assert ("pkg.util", "pkg.external") in graph.edges


def test_external_imports_are_dropped(make_project):
    # external.py imports json and os; neither lives in the tree
    graph = build_graph(scan_tree(make_project))

    assert all(src != "pkg.external" for src, _ in graph.edges)


def test_unparsable_modules_are_excluded(make_project):
    graph = build_graph(scan_tree(make_project))

    assert "broken" not in graph.nodes


def test_dot_output(make_project):
    dot = build_graph(scan_tree(make_project)).to_dot()

    assert dot.startswith("digraph codeatlas {")
    assert '"pkg.util" -> "pkg.core";' in dot


def test_no_self_edges(make_project):
    graph = build_graph(scan_tree(make_project))

    assert all(src != dst for src, dst in graph.edges)
