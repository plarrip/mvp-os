# MVP-OS

[![CI](https://github.com/plarrip/mvp-os/actions/workflows/ci.yml/badge.svg)](https://github.com/plarrip/mvp-os/actions/workflows/ci.yml)

**A product operating system for AI coding agents.** It keeps an agent honest
about *what is worth building and why*, before it writes a line of code.

Ask an agent to build something and it will build it. That is the problem.

```text
   what usually happens              what MVP-OS makes happen

     idea                              observation
      │                                    │
      ▼                                    ▼
     code                              problem ──▶ hypothesis
      │                                              │
      ▼                                              ▼
   a product nobody                             experiment ──▶ evidence
   asked for                                                     │
                                                                 ▼
                                                    decision ◀── learning
                                                        │
                                                        ▼
                                                     a product
                                                  someone wanted
```

The agent does the thinking. MVP-OS holds the state, checks it, and refuses to
let the process skip ahead.

---

## Two ways to run it

MVP-OS never writes code or specifications. It hands off.

```text
                      ┌──────────────────────────────┐
                      │           MVP-OS             │
                      │   "what to build, and why"   │
                      └───────────────┬──────────────┘
                                      │
                               mvp-os handoff
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
             STANDALONE                          WITH AN SDD TOOL
      the agent implements directly         /speckit-specify → plan → tasks
      from the handed-off context                   → implement
```

Both are first-class. Spec Kit is the SDD tool this was designed against and
tested with; the handoff itself is written so any other could read it. MVP-OS
**installs nothing** into your SDD tool and imports nothing from it.

---

## Getting started

```bash
uv tool install "git+https://github.com/plarrip/mvp-os"
# or: pipx install "git+https://github.com/plarrip/mvp-os"

cd your-project
mvp-os init
```

Then open your agent and say what you would have said anyway:

> *I want to start a new project. I have an idea for an app.*

You never have to mention MVP-OS. `init` leaves a trail the agent picks up on
its own:

```text
  CLAUDE.md ──▶ AGENTS.md ──▶ .mvp-os/methodology.md ──▶ .mvp-os/state.yml
   one line      how to        what the method is         where this
                 behave        and why                    project stands
```

Instead of writing code, the agent will ask who has the problem, what they do
today, and what you actually observed.

> **Using an SDD tool?** Initialize it *first* — `specify init --here`, then
> `mvp-os init`. Detection only happens during `init`. If you get the order
> wrong, re-run `mvp-os init` and check with `mvp-os status`.

---

## The nine gates

A project is always at one gate. Each one asks a question, and you cannot leave
until it is answered.

```text
  G0 ─▶ G1 ─▶ G2 ─▶ G3 ─▶ G4 ─▶ G5 ─▶ G6 ─▶ G7 ─▶ G8 ─┐
                ▲                                      │
                └──────────────────────────────────────┘
                  new evidence turns the loop again
```

| | Gate | The question it answers |
|---|---|---|
| **G0** | Intake | What is the idea, and where did it come from? |
| **G1** | Problem / User | Who has this problem, and what do they do today? |
| **G2** | Hypotheses | What must be true for this to work? |
| **G3** | Validation Strategy | What is the cheapest way to find out? |
| **G4** | Product Definition | What is the smallest thing worth building? |
| **G5** | SDD / Technical | How do we specify it? *(hands off here)* |
| **G6** | MVP Readiness | Can this ship? |
| **G7** | MVP Validation | Did it work? |
| **G8** | Learning / Decision | What did we learn, and what now? |

**It is a graph, not a ladder.** Evidence that kills a hypothesis sends a
project from G3 back to G2 — that is a success, not a failure. And G8 is where
the loop turns, not where it ends: a shipped MVP never leaves the lifecycle.

Jumping is what MVP-OS refuses:

```text
$ mvp-os transition G7
REJECTED
- transition G0 → G7 is not allowed

$ mvp-os transition G3
REJECTED
- at least one hypothesis is required
```

---

## Lenses

Every gate needs a different kind of thinking. MVP-OS names which ones apply,
and — when they disagree — which one wins.

```text
            G0  G1  G2  G3  G4  G5  G6  G7  G8
  lean      ●   ●   ●   ●   ●   ●   ●   ●   ●
  product       ●           ●
  validation            ●               ●
  technical                     ●   ●
  legal                             ●
  business                                  ●
  marketing                                 ●
```

| Lens | Grounded in | Where it speaks |
|---|---|---|
| **lean** | *The Lean Startup* (Ries) — riskiest assumption first, cheapest credible test | every gate |
| **product** | Double Diamond (Design Council), *Value Proposition Design* (Osterwalder) | G1, G4 |
| **validation** | Build-Measure-Learn; actionable over vanity metrics (Ries) | G3, G7 |
| **technical** | Feasibility and the cost of being wrong | G5, G6 |
| **legal** | What cannot ship, and what changes if it does | G6 |
| **business** | Business Model Canvas (Osterwalder & Pigneur) | G8 |
| **marketing** | Positioning and channel | G8 |

Three things this buys you.

**`lean` never leaves.** Drop it anywhere and the process drifts towards
building well instead of learning fast.

**Product design stops at G4.** Scope is settled there. Reopening it during
implementation is how an MVP stops being minimal.

**Business and marketing wait until G8.** Positioning a product nobody has used
is a guess dressed as strategy.

And the reason each gate names a winner: **frameworks contradict each other.**
Lean says ship the smallest thing now; Double Diamond says explore widely first.
Both are right somewhere. An agent handed both at once follows whichever it read
last — so G1 lets it diverge, and G2 does not.

Lenses are declared, never enforced. No tool can check how someone thought.

---

## Decisions

Before a decision at G8, and before abandoning work, the agent reasons in three
passes:

```text
   ☀  OPTIMISTIC     what could work — and what would have to be true?
        │
   ☁  SKEPTICAL      what breaks? which assumptions are load-bearing?
        │            what does the evidence not actually cover?
        ▼
   ⚖  JUDGEMENT      weigh both against the evidence on record, then decide
```

One line of reasoning will rationalise the hypothesis it wrote itself.
Separating proposal from refutation costs one extra pass and is the cheapest
correction available.

---

## Handing off

At G5 the product question is answered, and MVP-OS steps aside:

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

────────────────────────────────────────────────────────────
Hand to Spec Kit:  /speckit-specify  (paste everything above this line)
```

It carries what a specification cannot work out on its own: which hypotheses the
evidence actually supports, which are still guesses, and what you decided *not*
to build. Scope you ruled out is the most expensive thing to lose in a handoff —
nothing downstream remembers it was ever considered.

Run it too early and it refuses. A spec written before the product is defined is
the thing this tool exists to prevent.

---

## Commands

You will rarely type these — the agent does. They are there when you want to
check its work.

```bash
mvp-os init [--name NAME] [--description TEXT]   # set up, or refresh
mvp-os status                                    # where the project stands
mvp-os gate                                      # current gate and its lenses
mvp-os next                                      # the next action
mvp-os review                                    # gate plus evidence counts
mvp-os validate                                  # is the state coherent?
mvp-os transition <GATE>                         # the only way to change gate
mvp-os handoff                                   # emit the product context
mvp-os remove [--yes]                            # undo init
mvp-os --version                                 # which CLI you are running
```

The agent writes the thinking; MVP-OS checks it. There is deliberately no
`add-hypothesis` or `add-evidence` command — content belongs to the agent,
enforcement belongs here.

---

## Updating

When you run `mvp-os init`, it **copies** part of the method into your project:
`.mvp-os/methodology.md`, and a block inside `AGENTS.md`. Those copies are what
your agent reads every session — and they do not change when the tool changes.

```text
          THE TOOL                            YOUR PROJECTS
   ~/.local/.../mvp-os                 app-one/.mvp-os/methodology.md
                          init copies  app-two/.mvp-os/methodology.md
   updated once  ──────────────────▶   app-three/.mvp-os/methodology.md
                                       refreshed one by one
```

So updating takes two commands, in this order.

**1 · Update the tool**

```bash
uv tool install --force "git+https://github.com/plarrip/mvp-os"
mvp-os --version
```

**2 · Refresh each project that uses it**

```bash
cd app-one && mvp-os init
```

You do not have to remember which projects are behind. `mvp-os status` says so:

```text
Note: .mvp-os/methodology.md is outdated (CLI is 0.14.0) — run `mvp-os init` to update it
```

It stays quiet if you edited the methodology yourself. Being out of step on
purpose is a decision, not a problem.

> Use `--force` rather than `uv tool upgrade`, which will not move an install
> pinned to a tag: `...@v0.11.0` stays at v0.11.0, which is what a pin is for.

## Removing it

```bash
mvp-os remove          # shows exactly what it would touch, changes nothing
mvp-os remove --yes    # applies it
pip uninstall mvp-os
```

It deletes what it created and cuts out what it added, leaving your own rules in
`AGENTS.md`, your notes in `CLAUDE.md`, and your code untouched. A `.gitignore`
you already had keeps its `.venv/` line, because that line is indistinguishable
from one you would have written.

Files already committed stay in git history. If that matters, do not commit
`.mvp-os/` — it is your reasoning, not your product.

---

## More

| | |
|---|---|
| [`.mvp-os/methodology.md`](src/mvp_os/resources/methodology.md) | The method itself — gates, lenses, evidence model. What the agent reads |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How it is built, and why the Spec Kit bundle was not reinstated |
| [TESTING.md](TESTING.md) | Running the suite, and the manual tests automation cannot cover |
| [CHANGELOG.md](CHANGELOG.md) | What changed, and what it cost |

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

## License

MIT.
