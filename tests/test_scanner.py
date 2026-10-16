"""Scanner tests against the hand-counted sample project."""

from codeatlas.scanner import scan_tree


def test_module_inventory(make_project):
    report = scan_tree(make_project)

    paths = {m.path for m in report.modules}
    assert paths == {
        "pkg/__init__.py",
        "pkg/core.py",
        "pkg/util.py",
        "pkg/external.py",
        "broken.py",
    }  # notes.txt is not Python and must not appear


def test_totals(make_project):
    report = scan_tree(make_project)

    assert report.totals["modules"] == 5
    assert report.totals["classes"] == 1  # Engine
    assert report.totals["functions"] == 5  # simple, branching, run, twice, load
    assert report.totals["syntax_errors"] == 1  # broken.py


def test_function_details(make_project):
    report = scan_tree(make_project)

    core = next(m for m in report.modules if m.path == "pkg/core.py")
    by_name = {f.qualname: f for f in core.functions}

    assert set(by_name) == {"simple", "branching", "Engine.run"}
    assert by_name["simple"].complexity == 1
    assert by_name["branching"].complexity == 8
    assert by_name["Engine.run"].complexity == 2
    assert by_name["Engine.run"].params == 2  # self + mode
    assert by_name["simple"].has_docstring is False
    assert by_name["branching"].loc == 10


def test_class_details(make_project):
    report = scan_tree(make_project)

    core = next(m for m in report.modules if m.path == "pkg/core.py")
    engine = core.classes[0]

    assert engine.name == "Engine"
    assert engine.methods == 1
    assert engine.has_docstring is True


def test_relative_imports_recorded(make_project):
    report = scan_tree(make_project)

    util = next(m for m in report.modules if m.path == "pkg/util.py")
    assert ".core" in util.imports


def test_syntax_error_is_reported_not_raised(make_project):
    report = scan_tree(make_project)

    broken = next(m for m in report.modules if m.path == "broken.py")
    assert broken.syntax_error is not None
    assert "line 1" in broken.syntax_error


def test_skip_directories(make_project):
    (make_project / ".venv" / "lib").mkdir(parents=True)
    (make_project / ".venv" / "lib" / "hidden.py").write_text("x = 1\n")
    (make_project / "__pycache__").mkdir()
    (make_project / "__pycache__" / "junk.py").write_text("y = 2\n")

    report = scan_tree(make_project)

    assert all(".venv" not in m.path and "__pycache__" not in m.path for m in report.modules)
    assert report.totals["modules"] == 5
