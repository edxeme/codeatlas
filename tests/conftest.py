"""Shared fixtures: a tiny sample project with known, hand-counted facts."""

from pathlib import Path

import pytest

SAMPLE_FILES: dict[str, str] = {
    "pkg/__init__.py": '"""Sample package."""\n',
    "pkg/core.py": '''"""Core routines with hand-counted complexity."""


def simple(x):
    return x + 1


def branching(items, flag):
    total = 0
    for item in items:            # for +1
        if item % 2:              # if +1
            total += item
        elif flag and total:      # elif +1, and +1
            total -= item
    while total > 100:            # while +1
        total //= 2
    return [i for i in items if i]  # comprehension +1, filter +1


class Engine:
    """A trivial engine."""

    def run(self, mode="fast"):
        if mode == "fast":        # if +1
            return 1
        return 0
''',
    "pkg/util.py": '''"""Helpers that reuse core."""

from .core import simple


def twice(x):
    return simple(x) * 2
''',
    "pkg/external.py": '''"""Talks to the outside world."""

import json


def load(path):
    with open(path) as fh:
        return json.load(fh)
''',
    "broken.py": "def oops(:\n",
    "notes.txt": "not python\n",
}


@pytest.fixture
def make_project(tmp_path: Path) -> Path:
    """Write the sample project into a tmp dir and return its root."""
    root = tmp_path / "sample"
    for rel, content in SAMPLE_FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root
