# Changelog

## Unreleased

Hardening pass over the v0.7.0 baseline. No new features.

### Fixed

- **`mvp-os init` crashed on every real installation.** `package-data` used the
  glob `resources/*.md`, so `gitignore.template` never shipped, and `cli.py`
  read it unconditionally. The framework's entry point was broken for anyone
  without the source tree on disk.
- `mvp-os status`, `gate`, `next` and `review` raised a bare `AttributeError` on
  a malformed state. They now report what is wrong and exit non-zero.
- `validate` produced one error per character when a list field held a string.
- `init` silently overwrote a project's `.mvp-os/methodology.md`, discarding
  local adaptations. It now keeps a modified file and says so.
- `init --name` / `--description` were parsed and discarded on an
  already-initialized project. They are now applied and reported.
- Restored the MIT `LICENSE` file, dropped in v0.7.0 while `pyproject.toml`
  still declared the licence.

### Changed

- **`transition` no longer writes `next_action`.** It used to overwrite the
  field with `"Work on <Gate>."`, destroying the agent's own reasoning at the
  moment a gate change carries the most information. It now clears the field;
  `validate` requires it while a project is active.

  Consequence: gates can no longer be chained without declaring intent at each
  one. Plan, then move.

### Added

- Test suite (77 tests) covering brief tests A–E and G, including a packaging
  guard that builds and installs a real distribution from a staged clean copy —
  without which `build/lib` reuse and pip's wheel cache let the test pass over a
  broken artifact.
- `validate_shape()`, separating type errors from completeness errors.
- GitHub Actions CI: the suite across Python 3.9–3.14, plus a job that installs
  from a clean checkout and drives `init`, `validate` and a refused transition.
  `requires-python = ">=3.9"` was a claim nobody had ever executed.

## 0.7.0

Added the lifecycle transition graph, per-gate requirements, per-entry state
validation, `mvp-os transition`, and packaged `methodology.md` via
`importlib.resources`. Removed the dead `providers.py`.

Also removed, without replacement: the entire test suite, the `LICENSE`, and the
Spec Kit bundle (extension, five commands, two workflows) that `bundle.yml` and
`extension.yml` had declared. The Spec Kit integration has been unimplemented
since.

## 0.4.0

Restored the requirement that MVP-OS works without an SDD framework. Earlier
versions over-coupled it to Spec Kit.
