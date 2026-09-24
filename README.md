# MVP-OS

[![CI](https://github.com/plarrip/mvp-os/actions/workflows/ci.yml/badge.svg)](https://github.com/plarrip/mvp-os/actions/workflows/ci.yml)

A product-development operating system that turns an idea into a validated MVP,
lean. It is not primarily a programming framework.

It exists to stop `idea → code → product` and replace it with
`observation → problem → hypothesis → experiment → evidence → learning →
decision → product`.

The LLM is the brain: it converses, reasons, researches, forms hypotheses,
designs experiments, interprets evidence and proposes decisions. MVP-OS is the
control system: it holds persistent state, validates it, and refuses invalid
lifecycle transitions.

## Install

MVP-OS is a tool you use across projects, not a dependency of any one of them.
Install it once, globally, with `uv tool` or `pipx`:

```bash
uv tool install "git+https://github.com/plarrip/mvp-os@v0.9.0"
# or: pipx install "git+https://github.com/plarrip/mvp-os@v0.9.0"

cd your-project
mvp-os init
```

Both keep it in its own isolated environment while putting `mvp-os` on your
PATH. It never enters your project's dependencies -- no entry in your
`pyproject.toml`, `requirements.txt` or `package.json`.

Installing into a project's virtualenv also works, but then `mvp-os` only
exists while that virtualenv is active -- and `AGENTS.md` tells the agent to run
`mvp-os validate`, which would fail in any session that did not activate it.

To work on MVP-OS itself, install it from a checkout and skip the reinstall
step after every edit:

```bash
uv tool install --editable /path/to/mvp-os
```

`init` writes `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), `.mvp-os/state.yml` and
`.mvp-os/methodology.md`, and protects `.venv/` in `.gitignore`. It detects Spec
Kit if present. Re-running it is safe: existing instruction files are appended
to, not replaced, and a locally modified methodology is kept.

From then on an agent discovers MVP-OS on its own — no need to say "use
MVP-OS":

```text
CLAUDE.md → AGENTS.md → .mvp-os/methodology.md → .mvp-os/state.yml
```

## CLI

```bash
mvp-os init [--name NAME] [--description TEXT]   # set up or refresh a project
mvp-os status                                    # project, gate, provider, next action
mvp-os gate                                      # current gate only
mvp-os next                                      # next action only
mvp-os review                                    # gate plus evidence counts
mvp-os validate                                  # deterministic checkpoint
mvp-os transition <GATE>                         # the only way to change gate
mvp-os handoff                                   # emit the product context for an SDD provider
mvp-os remove [--yes]                            # undo init; without --yes, only plans
```

The CLI deliberately has no write commands for hypotheses, evidence or
decisions. Content flexibility belongs to the agent; enforcement belongs to
MVP-OS.

## Enforcement

The agent edits `.mvp-os/state.yml` freely, but cannot simply write
`current_gate: G7` and skip the process. Gate changes go through `transition`,
which checks three things in order: the state is structurally valid, the move
is allowed by the lifecycle graph, and the destination's requirements are met.

```text
$ mvp-os transition G7
REJECTED
- transition G0 → G7 is not allowed

$ mvp-os transition G3
REJECTED
- at least one hypothesis is required

$ mvp-os transition G1
ACCEPTED
G0 → G1 — Problem / User
next_action cleared. Set it in .mvp-os/state.yml; validate will fail until you do.
```

The lifecycle is a graph, not a ladder: `G3 → G2` is a valid move when evidence
invalidates a hypothesis. `G0 → G7` never is.

`validate` is a deterministic checkpoint, not a key-presence check. It rejects
bad schema versions, wrong types, non-mapping entries, missing and duplicate
ids, dangling references, invalid enums, and a current gate whose requirements
are no longer met.

## SDD integration

```text
MVP-OS            "What should we build and why?"
   ↓  mvp-os handoff
SDD provider      "How should we specify and implement it?"
```

MVP-OS works with no SDD framework at all, and alongside one. The seam between
them is a single command:

```text
$ mvp-os handoff
MVP-OS handoff — G5 · SDD provider: spec-kit

TARGET USER
  Solo technical founder

PROBLEM
  Jumps from idea to code without validating

VALIDATED HYPOTHESES
  H1  A solo founder would pay for process structure
      metric: >=8 of 20 name it unprompted
      EV1  9 of 20 named it unprompted

UNVALIDATED ASSUMPTIONS — carry into the spec as risks
  H2  Teams would adopt it alongside an existing process (risk: medium)

MVP SCOPE
  - single-hypothesis tracker

OUT OF SCOPE — do not specify
  - multi-user

--------------------------------------------------------------------
Hand to Spec Kit:  /speckit-specify  (paste everything above this line)
```

It refuses before G5: a specification written before the product is defined is
the thing MVP-OS exists to prevent.

### Order matters

Initialize the SDD provider first:

```bash
specify init --here          # then
mvp-os init
```

Detection happens during `mvp-os init` and nowhere else. If Spec Kit arrives
afterwards, `sdd.provider` stays `none` until you re-run `mvp-os init`, which
syncs it. Check with `mvp-os status`.

### Only Spec Kit, so far

Spec Kit is the only provider this has been designed against and tested with.
The handoff itself is provider-agnostic by construction -- the block is the same
whoever reads it -- so nothing structural blocks OpenSpec, Superpowers or
another SDD framework. But detection, and the closing line that names a
provider, know about Spec Kit only. If there is demand for another, the
integration is small work; it is simply not done or verified today.

Two properties are deliberate. The block is identical whoever picks it up --
only the closing line names a provider -- so the core never becomes a wrapper
around one SDD framework. And MVP-OS **installs nothing** into Spec Kit: no
extension, no commands, no templates. Spec Kit owns specification and
implementation; duplicating its primitives inside MVP-OS would dissolve the
boundary the handoff exists to draw.

What the handoff carries is what a spec cannot reconstruct on its own: which
hypotheses evidence actually supports, which are still assumptions, and what was
explicitly ruled out. Scope that was decided against is the most expensive thing
to lose in a handoff, because nothing downstream records that it was ever
considered.

## Removing it

```bash
mvp-os remove          # prints exactly what it would touch, changes nothing
mvp-os remove --yes    # applies it
pip uninstall mvp-os
```

It deletes what it created and cuts out what it added, leaving everything else
alone: your own rules in `AGENTS.md`, your notes in `CLAUDE.md`, and your code.
A `.gitignore` it created is deleted; one you already had keeps its `.venv/`
line, because that line is indistinguishable from one you would have written.

Files already committed stay in git history. If that matters, do not commit
`.mvp-os/` in the first place -- it is your reasoning process, not your product.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

See [TESTING.md](TESTING.md).

## License

MIT.
