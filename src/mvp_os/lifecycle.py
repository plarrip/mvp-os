"""The lifecycle graph and what each gate demands before it can be entered."""
from __future__ import annotations

from typing import Any

GATES = {
    "G0": "Intake",
    "G1": "Problem / User",
    "G2": "Hypotheses",
    "G3": "Validation Strategy",
    "G4": "Product Definition",
    "G5": "SDD / Technical Definition",
    "G6": "MVP Readiness",
    "G7": "MVP Validation",
    "G8": "Learning / Decision",
}

# A graph, not a ladder. Evidence can send a project backwards: G3 -> G2 is a
# normal move when a hypothesis is invalidated, and a failed MVP must be able to
# fall back to product reasoning rather than only stopping. What stays forbidden
# is skipping: G0 -> G7 has no path.
TRANSITIONS = {
    "G0": {"G1"},
    "G1": {"G0", "G2"},
    "G2": {"G1", "G3"},
    "G3": {"G2", "G4"},
    "G4": {"G3", "G5"},
    "G5": {"G4", "G6"},
    "G6": {"G5", "G7"},
    "G7": {"G6", "G8", "G2", "G3", "G4"},
    "G8": {"G2", "G3", "G4", "G5", "G6", "G7"},
}


GATE_ORDER = tuple(GATES)


def gate_index(gate: str) -> int:
    """Position in the lifecycle. The graph allows loops, but "have we reached
    product definition yet" is still a linear question."""
    return GATE_ORDER.index(gate) if gate in GATES else -1


def gate_name(gate: str) -> str:
    return GATES.get(gate, "Unknown")


def is_valid_gate(gate: Any) -> bool:
    return gate in GATES


def transition_allowed(current: Any, target: Any) -> bool:
    return target in TRANSITIONS.get(current, set())


def gate_requirements_satisfied(data: dict[str, Any], target: str) -> list[str]:
    """What is still missing before `target` can be entered.

    These are floors, not checklists: meeting them does not mean a gate should
    be passed, but failing them means it cannot be. Deliberately minimal -- they
    exist to catch absurd states, not to manufacture documentation.
    """
    errors: list[str] = []
    project = data.get("project", {})
    problem = data.get("problem", {})
    hypotheses = data.get("hypotheses", [])
    experiments = data.get("experiments", [])
    evidence = data.get("evidence", [])
    learnings = data.get("learnings", [])
    decisions = data.get("decisions", [])
    mvp = data.get("mvp", {})
    sdd = data.get("sdd", {})

    if target == "G1":
        if not project.get("description"):
            errors.append("project.description is required")
        if not problem.get("user"):
            errors.append("problem.user is required")

    elif target == "G2":
        if not problem.get("user"):
            errors.append("problem.user is required")
        if not problem.get("problem"):
            errors.append("problem.problem is required")

    elif target == "G3":
        if not hypotheses:
            errors.append("at least one hypothesis is required")
        for i, hypothesis in enumerate(hypotheses):
            if not isinstance(hypothesis, dict):
                errors.append(f"hypotheses[{i}] must be a mapping")
                continue
            for field in ("id", "statement", "risk", "test", "success_metric"):
                if not hypothesis.get(field):
                    errors.append(f"hypotheses[{i}].{field} is required")

    elif target == "G4":
        if not hypotheses:
            errors.append("at least one hypothesis is required")
        if not experiments:
            errors.append("at least one validation experiment is required")

    elif target == "G5":
        if not mvp.get("scope"):
            errors.append("mvp.scope must be defined")
        # Standalone is fine, but it has to be a decision rather than an oversight.
        if sdd.get("provider") == "none" and sdd.get("status") != "not_required":
            errors.append("without an SDD provider, set sdd.status to 'not_required'")

    elif target == "G6":
        if not mvp.get("scope"):
            errors.append("mvp.scope must be defined")
        if sdd.get("provider") != "none" and sdd.get("status") not in {"ready", "active"}:
            errors.append("SDD provider must be ready or active")

    elif target == "G7":
        if not mvp.get("scope"):
            errors.append("mvp.scope must be defined")
        if not decisions and not evidence:
            errors.append(
                "evidence or an explicit decision is required before MVP validation"
            )

    elif target == "G8":
        if not evidence:
            errors.append("at least one evidence item is required")
        if not learnings:
            errors.append("at least one learning is required")
        if not decisions:
            errors.append("at least one decision is required")

    return errors
