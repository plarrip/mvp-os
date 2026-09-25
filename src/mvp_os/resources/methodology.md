# MVP-OS Methodology

MVP-OS is the product-learning layer for taking an idea toward a validated MVP.
It exists to replace `idea → code → product` with
`observation → problem → hypothesis → experiment → evidence → learning → decision → product`.

## Operating model

The agent owns product reasoning and the contents of `.mvp-os/state.yml`:
problem, hypotheses, experiments, evidence, learnings, decisions, MVP scope.
MVP-OS owns enforcement: it validates state and accepts or refuses gate
transitions, and writes no product content of its own.

How to operate that division day to day is in the agent instructions, not here.

## Lifecycle

G0 Intake → G1 Problem/User → G2 Hypotheses → G3 Validation Strategy →
G4 Product Definition → G5 SDD/Technical Definition → G6 MVP Readiness →
G7 MVP Validation → G8 Learning/Decision.

The lifecycle is a graph, not a ladder. Evidence can move a project forward,
backward, pause it or stop it. G3 → G2 is a normal move when a hypothesis is
invalidated. G0 → G7 is never valid.

G8 is a turning point, not a finish line. A shipped MVP does not leave the
lifecycle: evidence keeps arriving, and G8 leads back to G2, G3 or G4 for the
next round. The loop does not stop when a product exists, or when a business
does. Treat "Learning / Decision" as the place the cycle turns, never as the end
of it.

A paused or stopped project cannot change gates. Something was decided about
it; resuming is that decision being reversed, and has to be recorded as one by
setting `lifecycle.status` back to `active`.

## Gate requirements

A gate is passed because decision-relevant evidence is sufficient, not because
documentation is complete. The minimum MVP-OS enforces:

| Gate | Requires |
|---|---|
| G1 Problem / User | `project.description`, `problem.user` |
| G2 Hypotheses | `problem.user`, `problem.problem` |
| G3 Validation Strategy | ≥1 hypothesis with `id`, `statement`, `risk`, `test`, `success_metric` |
| G4 Product Definition | ≥1 hypothesis and ≥1 experiment |
| G5 SDD / Technical Definition | `mvp.scope`; with no provider, `sdd.status: not_required` |
| G6 MVP Readiness | `mvp.scope`; a configured provider must be `ready` or `active` |
| G7 MVP Validation | `mvp.scope`, plus evidence or an explicit prior decision |
| G8 Learning / Decision | ≥1 evidence, ≥1 learning, ≥1 decision |

These are floors, not checklists. Meeting them does not mean a gate should be
passed; failing them means it cannot be.

## Lenses

Each gate calls for particular ways of reasoning. Roles, not steps: nothing
checks that they were used, and no gate requires them.

| Gate | Lenses | Last word |
|---|---|---|
| G0 Intake | lean | capture, do not judge yet |
| G1 Problem / User | product, lean | double diamond; diverging on the problem is correct here |
| G2 Hypotheses | lean | Lean Startup; here diverging is procrastination |
| G3 Validation Strategy | lean, validation | cheapest credible experiment beats the most rigorous |
| G4 Product Definition | lean, product | scope is the decision, and less is the default |
| G5 SDD / Technical | lean, technical | feasibility, and the cost of being wrong |
| G6 MVP Readiness | lean, technical, legal | what cannot ship |
| G7 MVP Validation | lean, validation | actionable metrics over flattering ones |
| G8 Learning / Decision | lean, business, marketing | now there is something real to position |

`lean` is present at every gate; without it the process drifts towards building
well instead of learning fast.

Frameworks conflict, so each gate names one that decides. Lean says ship the
smallest thing now, design thinking says explore widely first; given both at
once, an agent follows whichever it read last. Product design leaves after G4:
reopening scope during implementation is how an MVP stops being minimal.

## Decisions

Before a decision at G8, and before any transition that abandons work, reason in
three passes:

1. **Optimistic** — what could work, and what would have to be true for it to.
2. **Skeptical** — what fails, which assumptions are load-bearing, what the
   evidence does not cover.
3. **Judgement** — weigh both against the evidence on record, then decide.

One line of reasoning rationalises the hypothesis it wrote itself. Separating
proposal from refutation costs one pass and is the cheapest correction there is.

## Evidence model

OBSERVATION → ASSUMPTION → HYPOTHESIS → EXPERIMENT → EVIDENCE → LEARNING → DECISION.

Keep observation separate from interpretation. Never invent evidence.

## Lean doctrine

- Identify important assumptions before building.
- Prioritise the riskiest hypothesis first.
- Prefer the cheapest credible experiment. Manual, fake, prototype and
  concierge tests are valid.
- Do not optimize an assumption that has not been validated.
- Do not expand MVP scope without explicit value or learning justification.
- Keep conversations bounded and action-oriented; avoid open-ended research.
- If evidence is insufficient: state `INSUFFICIENT EVIDENCE`, say what is
  missing, and stop.

The recurring question: what is the smallest action that can produce meaningful
validated learning?

## SDD boundary

MVP-OS owns product discovery, hypotheses, experiments, evidence, learning,
decisions and MVP scope — *what should we build and why*.

An SDD provider owns technical specification, design and implementation
workflow — *how should we specify and build it*. MVP-OS does not duplicate
those primitives.
