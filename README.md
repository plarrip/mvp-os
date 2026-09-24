# MVP-OS

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

```bash
pip install /path/to/mvp-os
cd your-project
mvp-os init
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

MVP-OS must work with no SDD framework at all, and alongside one. Spec Kit is
the reference integration, and it is **not finished**: `init` detects Spec Kit
and records it in `sdd.provider`, but the bundle that would install its
commands was removed in v0.7.0 and has not been reinstated.

```text
MVP-OS            "What should we build and why?"
   ↓
SDD provider      "How should we specify and implement it?"
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

See [TESTING.md](TESTING.md).

## License

MIT.
