# Changelog

## 0.16.1

### Fixed

- `mvp-os remove` told you to run `pip uninstall mvp-os`. The README had
  already been corrected; the message in the code had not, so the fix reached
  the documentation and not the product. Found by running the whole
  install-use-update-uninstall cycle with the README's own commands, which is
  what nothing had ever done.

  It now names the tools that can actually work: `uv tool uninstall` or `pipx
  uninstall`.

### Documentation

- The removal instructions said `pip uninstall mvp-os`, while the install
  instructions said `uv tool` and `pipx`. Those install into their own
  environments, so pip cannot see the package — and on a machine without a
  virtualenv active there is often no `pip` on PATH at all, which is how a user
  hit it. Corrected, and the two removals are now clearly separate: out of one
  project, and off the machine.

## 0.16.0

### Fixed

- `mvp-os sync` now re-runs SDD provider detection. Detection ran during `init`
  alone, which was coherent while `init` was the only way to refresh anything;
  once sync became the documented update path, a project that gained a provider
  afterwards was being told to run the one command that could not notice it.

  Found by walking a fresh project through both flows end to end, not by
  reading the code: the gap was introduced one release earlier and reads
  perfectly well on the page.

  Sync still refreshes the copied files when the state cannot be parsed, and
  says it skipped the provider check. The command people reach for when a
  project is broken must not depend on the part that is broken.

## 0.15.0

### Added

- `mvp-os sync`: refresh a project's copied files after upgrading the CLI.
  `init` already did this and still does — sync exists because the verb
  matters. Nobody looking for how to update reads the help for a command called
  `init`, and a tool saying "this is outdated, run `init`" reads like a
  mistake. The outdated-methodology note now names `sync`.

### Documentation

- The update instructions recommended `uv tool install --force`, which is
  "install" used to mean "upgrade". `uv tool upgrade mvp-os --reinstall` is the
  correct command and was verified to re-fetch from git. `--force` install is
  now mentioned only for changing a pinned version.

## 0.14.0

### Added

- `mvp-os --version`. In a tool where version drift between the CLI and a
  project's installed files is a real failure mode, not being able to ask it
  which version it is was an odd gap. The outdated-methodology note now names
  the CLI version too, so "outdated" says what it is outdated against.

  The version comes from package metadata rather than a constant in the source,
  which is one fewer thing that can disagree with pyproject.toml. Note that an
  editable install reports the version recorded when it was installed, so bump
  and reinstall together.

- A test that the version in pyproject.toml has a CHANGELOG entry. Bumping
  without writing down what changed is the drift worth catching.

### Documentation

- README gains an Updating section: both layers, and why `uv tool upgrade` will
  not move a tag-pinned install.

## 0.13.0

### Added

- `mvp-os status` reports when `.mvp-os/methodology.md` has fallen behind the
  installed CLI. Files sync only during `init`, so a long-running project could
  sit several versions behind the method being enforced, with nothing saying so
  — and that file is what the agent reads every session.

  Only when the recorded digest proves the project did not edit it. Being out of
  step deliberately is a decision, not a problem to report, and no digest means
  local edits cannot be ruled out.

## 0.12.0

### Added

- Lenses: each gate declares the reasoning roles it calls for, and which
  framework has the last word when they disagree. `lean` at every gate, product
  design only through G4, business and marketing not before G8. `mvp-os gate`
  prints the active ones.

  Declared, never enforced — no tool can validate that someone reasoned a
  certain way — and never executed: how a lens is realised belongs to the agent
  harness, as specification belongs to the SDD provider.

- A three-pass decision procedure (optimistic, skeptical, judgement) for G8 and
  for transitions that abandon work.

- Drift guards: the methodology's lens and requirement tables are now checked
  against the code. The requirements table had only ever been verified by eye.

### Changed

- The methodology states that G8 is where the cycle turns, not where it ends. A
  shipped MVP does not leave the lifecycle.

  Cost: the per-session read grows from roughly 1,025 to 1,627 tokens. Almost
  all of it is the lens table, which is the feature.

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
