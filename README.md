# codeatlas

[![CI](https://github.com/edxeme/codeatlas/actions/workflows/ci.yml/badge.svg)](https://github.com/edxeme/codeatlas/actions/workflows/ci.yml)
[![PyPI — python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://pypi.org/project/codeatlas/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: stdlib only](https://img.shields.io/badge/dependencies-stdlib%20only-success)](#how-it-works)

Map any Python codebase — module inventory, complexity hotspots and internal
import graph — straight from the AST, with zero third-party dependencies.

```sh
$ codeatlas scan src
module                                         loc  cls  fns    cx  imp
-----------------------------------------------------------------------
codeatlas/__init__.py                            3    0    0     0    0
codeatlas/__main__.py                            8    0    0     0    3
codeatlas/cli.py                               125    0    6    21   12
codeatlas/complexity.py                         53    0    2     9    3
codeatlas/graph.py                             103    1    6    37    8
codeatlas/scanner.py                           218    5   14    47   11
-----------------------------------------------------------------------
6 modules · 510 loc · 6 classes · 28 functions
```

That is codeatlas scanning *itself* — the fastest way to see what it does.

## Why

Before you refactor or onboard onto a codebase you need a map: which modules
are big, which functions hide the branching, what depends on what. codeatlas
answers those three questions in one pass over `ast` — no indexing service,
no config, no plugins to install.

## Install

```sh
pipx install codeatlas        # or: pip install codeatlas
```

Requires Python 3.11+.

## Usage

**Inventory** — `codeatlas scan PATH`

One row per module: lines of code, class/function counts, summed cyclomatic
complexity, import count. Files that cannot be parsed are listed as warnings
on stderr; the scan never dies on one bad file.

**Hotspots** — `codeatlas hotspots PATH [-n N]`

The most complex functions first — complexity, then size, then qualname so
ties are deterministic — with `file:line` locations ready to jump to:

```sh
$ codeatlas hotspots src -n 5
  cx  location                                         function
---------------------------------------------------------------
  15  codeatlas/graph.py:81                            build_graph
   9  codeatlas/scanner.py:172                         _ModuleVisitor.visit_ImportFrom
   8  codeatlas/cli.py:99                              main
   8  codeatlas/scanner.py:98                          iter_python_files
   7  codeatlas/graph.py:33                            _relative_target
```

**Import graph** — `codeatlas graph PATH`

Internal dependencies as Graphviz DOT; render with
`codeatlas graph . | dot -Tsvg > graph.svg`:

```sh
$ codeatlas graph src
digraph codeatlas {
  rankdir=LR;
  "codeatlas.__main__" -> "codeatlas.cli";
  "codeatlas.cli" -> "codeatlas.graph";
  "codeatlas.cli" -> "codeatlas.scanner";
  "codeatlas.graph" -> "codeatlas.scanner";
  "codeatlas.scanner" -> "codeatlas.complexity";
}
```

**JSON everywhere** — add `--json` to any command when a dashboard or script
is the real consumer. See the bundled `sample/` warehouse app for a tiny
project to scan.

## How it works

- **One AST pass per file.** A `NodeVisitor` collects modules, classes and
  functions (qualnames included) plus raw import statements. `ast.parse`
  reports what it cannot parse instead of failing the scan.
- **Scope-aware complexity.** Cyclomatic complexity counts one point per
  branch a function *owns* — `if`/`for`/`while`, `except` handlers, ternaries,
  `assert`, boolean operators, comprehension clauses and `match` cases.
  Nested functions and lambdas are scored separately: their decisions never
  inflate the enclosing scope.
- **Path-based import resolution.** Relative imports resolve against the
  importing file's directory; absolute imports match dotted names derived
  from the tree (`src/` prefixes are trimmed so src-layout resolves).
  Anything unmatched — stdlib, third-party — is external and dropped.

## Docker

The image installs the package and runs a self-contained smoke test against
the bundled sample:

```sh
docker build -t codeatlas .
docker run --rm codeatlas
```

## Development

```sh
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/pytest            # 33 tests, all stdlib-speed
```

## Roadmap

- [ ] `--watch` mode for live re-scans while editing
- [ ] Optional complexity thresholds with non-zero exit codes for CI gates
- [ ] Markdown/HTML report renderer alongside DOT and JSON

## License

[MIT](LICENSE) — Edwin Martinez
