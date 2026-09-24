# Changelog

## 0.11.0

### Added

- `mvp-os handoff`: emits the validated product context for an SDD provider to
  specify. It carries what a specification cannot reconstruct -- which
  hypotheses evidence supports, which are still assumptions, and what was
  explicitly ruled out -- and refuses before G5.

  The block is provider-agnostic; only the closing line names Spec Kit. MVP-OS
  installs nothing into a provider.

- `validate` now checks `hypothesis_id` on evidence, learnings and decisions,
  not only on experiments. Evidence claiming to support a hypothesis that does
  not exist is worse than evidence with no link.

### Note on the Spec Kit bundle

The v0.6.0 bundle was not reinstated. Tested against Spec Kit 1.0.11: a bundle
cannot carry its own extension (`_locate_bundled_extension` reads only Spec
Kit's core pack or checkout), so it cannot be installed offline even when the
built artifact embeds it; and its commands used the wrong namespace. Both are
fixable, but the five commands restate guidance the methodology already gives,
coupled to one provider's extension format. See ARCHITECTURE.md.

## 0.10.0

### Fixed

- Every command that reads state raised a PyYAML stack trace when `state.yml`
  was not valid YAML. The agent writes that file by hand, so a syntax error is
  the likeliest failure in daily use, and six of eight commands answered it with
  a traceback. They now report the problem and the line.
- A `paused`, `stopped` or `completed` project could still change gates.
  `lifecycle.status` was validated but never enforced, which made it
  decoration. Transitions now require an active project.

### Changed

- The methodology no longer restates the operating instructions. Both files are
  read every session, so the overlap cost context on every run and left two
  places to update per rule.

## 0.9.0

### Added

- `mvp-os remove`, which undoes `init`. Without `--yes` it only prints the plan;
  it deletes `.mvp-os/state.yml`, so an accidental invocation would destroy a
  project's hypotheses, evidence and decisions.

  It removes what it created and cuts out what it added, and leaves alone
  anything it cannot prove it authored: a `.gitignore` the project already had
  keeps its `.venv/` line, because that line is indistinguishable from one the
  project would have written. Files already committed remain in git history.

  Deliberately absent from AGENTS.md: uninstalling is a decision for the person,
  not a step an agent should ever consider taking.

## 0.8.0

Hardening pass over the v0.7.0 baseline. No new features.

The minor bump is not cosmetic: `transition` no longer writes `next_action` and
`validate` now requires it, so a state or a script that worked against v0.7.0
can fail here. In pre-1.0 that is what a minor bump is for.

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
