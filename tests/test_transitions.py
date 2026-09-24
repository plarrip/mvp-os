"""Gate enforcement: the lifecycle is a graph, not a ladder (brief section 6)."""
from __future__ import annotations

import copy

import pytest

from mvp_os.lifecycle import (
    GATES,
    TRANSITIONS,
    gate_requirements_satisfied,
    is_valid_gate,
    transition_allowed,
)
from mvp_os.state import DEFAULT_STATE


@pytest.fixture
def state():
    return copy.deepcopy(DEFAULT_STATE)


HYPOTHESIS = {
    "id": "H1",
    "statement": "A solo founder would pay for process structure",
    "risk": "high",
    "test": "20 problem interviews",
    "success_metric": ">=8 of 20 name it unprompted",
}


def test_transition_map_only_references_real_gates():
    for origin, targets in TRANSITIONS.items():
        assert is_valid_gate(origin)
        for target in targets:
            assert is_valid_gate(target), f"{origin} -> {target} is not a gate"


def test_every_gate_is_reachable_from_G0():
    """No gate may be stranded: the graph must stay connected from intake."""
    seen, frontier = {"G0"}, ["G0"]
    while frontier:
        for target in TRANSITIONS.get(frontier.pop(), set()):
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    assert seen == set(GATES), f"unreachable gates: {set(GATES) - seen}"


def test_C_arbitrary_jump_is_refused():
    """Test C from the brief: G0 -> G7 must never be allowed."""
    assert not transition_allowed("G0", "G7")


@pytest.mark.parametrize("target", ["G2", "G3", "G4", "G5", "G6", "G8"])
def test_no_gate_skipping_from_intake(target):
    assert not transition_allowed("G0", target)


def test_E_evidence_can_move_a_project_backwards():
    """Test E: G3 -> G2 when new evidence invalidates a hypothesis."""
    assert transition_allowed("G3", "G2")


def test_late_gates_can_return_to_product_reasoning():
    """A failed MVP must be able to fall back to hypotheses, not just stop."""
    assert transition_allowed("G7", "G2")
    assert transition_allowed("G8", "G2")


def test_unknown_gate_is_not_a_valid_target():
    assert not is_valid_gate("G99")
    assert not transition_allowed("G0", "G99")


# --- destination requirements -------------------------------------------------

def test_G1_requires_a_described_project_and_a_user(state):
    assert gate_requirements_satisfied(state, "G1")
    state["project"]["description"] = "Lean MVP operating system"
    state["problem"]["user"] = "Solo technical founder"
    assert gate_requirements_satisfied(state, "G1") == []


def test_G2_requires_a_stated_problem(state):
    state["problem"]["user"] = "Solo technical founder"
    assert any("problem.problem" in e for e in gate_requirements_satisfied(state, "G2"))


def test_G3_requires_fully_formed_hypotheses(state):
    assert any("at least one hypothesis" in e for e in gate_requirements_satisfied(state, "G3"))
    state["hypotheses"] = [{"id": "H1", "statement": "vague"}]
    errors = gate_requirements_satisfied(state, "G3")
    assert any("risk is required" in e for e in errors)
    assert any("test is required" in e for e in errors)
    assert any("success_metric is required" in e for e in errors)
    state["hypotheses"] = [HYPOTHESIS]
    assert gate_requirements_satisfied(state, "G3") == []


def test_G4_requires_an_experiment_not_just_a_hypothesis(state):
    state["hypotheses"] = [HYPOTHESIS]
    assert any("experiment" in e for e in gate_requirements_satisfied(state, "G4"))


def test_G5_without_an_sdd_provider_demands_an_explicit_opt_out(state):
    """Standalone is fine, but it has to be a decision, not an oversight."""
    state["mvp"]["scope"] = ["single hypothesis tracker"]
    errors = gate_requirements_satisfied(state, "G5")
    assert any("not_required" in e for e in errors)
    state["sdd"]["status"] = "not_required"
    assert gate_requirements_satisfied(state, "G5") == []


def test_G6_requires_a_ready_sdd_provider_when_one_is_configured(state):
    state["mvp"]["scope"] = ["single hypothesis tracker"]
    state["sdd"] = {"provider": "spec-kit", "status": "not_started"}
    assert any("ready or active" in e for e in gate_requirements_satisfied(state, "G6"))
    state["sdd"]["status"] = "ready"
    assert gate_requirements_satisfied(state, "G6") == []


def test_G8_requires_the_full_evidence_chain(state):
    """Evidence -> learning -> decision. No shortcuts to a conclusion."""
    errors = gate_requirements_satisfied(state, "G8")
    assert len(errors) == 3
    state["evidence"] = [{"id": "EV1"}]
    state["learnings"] = [{"id": "L1"}]
    assert any("decision" in e for e in gate_requirements_satisfied(state, "G8"))
    state["decisions"] = [{"id": "D1"}]
    assert gate_requirements_satisfied(state, "G8") == []
