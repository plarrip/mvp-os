# MVP-OS Methodology

MVP-OS is the product-learning layer for taking an idea toward a validated MVP.
It exists to replace `idea → code → product` with
`observation → problem → hypothesis → experiment → evidence → learning → decision → product`.

## Operating model

The agent owns product reasoning and the contents of `.mvp-os/state.yml`:
problem, hypotheses, experiments, evidence, learnings, decisions, MVP scope.
MVP-OS owns enforcement and writes no product content.

- Edit state content directly, then run `mvp-os validate`.
- Never edit `lifecycle.current_gate`. Gate changes go through
  `mvp-os transition <GATE>`, which refuses invalid moves.
- **A transition clears `lifecycle.next_action`.** Write the new one before
  anything else: `validate` fails while an active project has none, and the
  next transition is refused until it is set. Stating where you are going is
  the price of moving.

## Lifecycle

G0 Intake → G1 Problem/User → G2 Hypotheses → G3 Validation Strategy →
G4 Product Definition → G5 SDD/Technical Definition → G6 MVP Readiness →
G7 MVP Validation → G8 Learning/Decision.

The lifecycle is a graph, not a ladder. Evidence can move a project forward,
backward, pause it or stop it. G3 → G2 is a normal move when a hypothesis is
invalidated. G0 → G7 is never valid.

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
