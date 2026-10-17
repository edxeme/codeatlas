"""CLI tests for the scan command."""

import pytest

from codeatlas.cli import main


def test_scan_text_output(make_project, capsys):
    assert main(["scan", str(make_project)]) == 0

    out = capsys.readouterr().out
    assert "pkg/core.py" in out
    assert "pkg/util.py" in out
    assert "5 modules" in out


def test_scan_warns_about_broken_files(make_project, capsys):
    assert main(["scan", str(make_project)]) == 0

    err = capsys.readouterr().err
    assert "broken.py" in err
    assert "could not parse 1 file(s)" in err


def test_hotspots_ranks_by_complexity(make_project, capsys):
    assert main(["hotspots", str(make_project)]) == 0

    out = capsys.readouterr().out
    rows = [
        line for line in out.splitlines() if line.strip() and not line.strip().startswith(("cx", "--"))
    ]
    assert "branching" in rows[0]  # complexity 8 outranks everything


def test_hotspots_respects_top_limit(make_project, capsys):
    assert main(["hotspots", str(make_project), "-n", "2"]) == 0

    out = capsys.readouterr().out
    rows = [
        line for line in out.splitlines() if line.strip() and not line.strip().startswith(("cx", "--"))
    ]
    assert len(rows) == 2


def test_hotspots_rejects_missing_path(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["hotspots", "/nonexistent/codeatlas-path"])

    assert excinfo.value.code == 1


def test_scan_rejects_missing_path(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["scan", "/nonexistent/codeatlas-path"])

    assert excinfo.value.code == 1
    assert "not a directory" in capsys.readouterr().err
