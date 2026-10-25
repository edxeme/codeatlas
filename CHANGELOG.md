# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] — 2026-10-27

### Added

- Docker image with a self-contained smoke test (`docker run` scans the bundled sample).
- GitHub Actions CI: pytest across Python 3.11–3.13 plus a self-scan smoke step.
- Full documentation: self-scan output, complexity model, Docker and development sections.

## [0.2.1] — 2026-10-27

### Fixed

- `hotspots -n 0` / negative `-n` now yield an empty ranking instead of slicing from
  the end of the list and showing the least complex functions.

### Hardened

- Regression tests pin scanner behavior on hostile inputs: bad encodings, NUL bytes
  and unparsable files are reported as warnings, never fatal.

## [0.2.0] — 2026-10-27

### Added

- `--json` output for `scan`, `hotspots` and `graph` for machine consumers.
- Internal import graph (`codeatlas graph PATH`) rendered as Graphviz DOT:
  relative imports resolve path-based, absolute imports match dotted names
  derived from the tree.

### Changed

- `codeatlas hotspots PATH [-n N]` ranks functions by complexity, then size,
  then qualname for deterministic ties.

## [0.1.0] — 2026-10-27

### Added

- Initial scaffold: hatchling packaging, MIT license, editor configuration.
- `codeatlas scan PATH`: single-pass AST inventory of modules, classes and
  functions — qualnames, params, docstrings, loc — with scope-aware cyclomatic
  complexity that never leaks nested-function decisions into enclosing scopes.
- Unparsable files are reported as warnings instead of aborting the scan.
