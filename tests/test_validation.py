"""`mvp-os validate` as a deterministic checkpoint (brief section 11)."""
from __future__ import annotations

import copy

import pytest
import yaml

from mvp_os.state import DEFAULT_STATE
from mvp_os.validation import validate_state


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

# The exact payload the brief calls out as something that must never validate.
CORRUPT_STATE = yaml.safe_load(
    """
schema_version: 99
project: "esto esta mal"
lifecycle: {current_gate: G7, status: active, next_action: null}
problem: {}
hypotheses:
  - "una hipotesis que es un string"
experiments: []
evidence: []
learnings: []
decisions: []
mvp: {}
sdd: {provider: spec-kit, status: inventado}
"""
)


def test_default_state_is_valid(state):
    assert validate_state(state) == []


def test_corrupt_state_is_rejected():
    """Regression: this exact state returned VALID before v0.7.0."""
    errors = validate_state(CORRUPT_STATE)
    assert errors
    joined = " | ".join(errors)
    for expected in (
        "schema_version",
        "project must be a mapping",
        "hypotheses[0] must be a mapping",
        "sdd.status",
    ):
        assert expected in joined, f"{expected!r} not reported in: {joined}"


def test_validation_is_at_least_as_strict_as_the_readers(state):
    """Nothing may validate that the read commands cannot parse.

    Section 11: never VALID if `mvp-os status` would then be unable to read it.
    """
    for key in ("project", "lifecycle", "sdd", "mvp", "problem"):
        broken = copy.deepcopy(state)
        broken[key] = "not a mapping"
        assert validate_state(broken), f"{key} as a string must not validate"


@pytest.mark.parametrize("bad", [99, "1", None, 2])
def test_unsupported_schema_version(state, bad):
    state["schema_version"] = bad
    assert any("schema_version" in e for e in validate_state(state))


def test_active_project_must_declare_a_next_action(state):
    """A transition clears next_action; validate is what makes filling it mandatory."""
    state["lifecycle"]["next_action"] = None
    assert any("next_action is required" in e for e in validate_state(state))


@pytest.mark.parametrize("status", ["paused", "stopped", "completed"])
def test_inactive_projects_need_no_next_action(state, status):
    state["lifecycle"].update({"status": status, "next_action": None})
    assert validate_state(state) == []


def test_missing_top_level_field(state):
    del state["hypotheses"]
    assert any("missing top-level field: hypotheses" in e for e in validate_state(state))


def test_entries_require_an_id(state):
    state["evidence"] = [{"note": "no id here"}]
    assert any("evidence[0].id is required" in e for e in validate_state(state))


def test_duplicate_ids_are_rejected(state):
    state["hypotheses"] = [HYPOTHESIS, dict(HYPOTHESIS)]
    assert any("duplicate id" in e for e in validate_state(state))


def test_experiment_referencing_unknown_hypothesis(state):
    state["hypotheses"] = [HYPOTHESIS]
    state["experiments"] = [{"id": "E1", "hypothesis_id": "H404"}]
    assert any("unknown hypothesis" in e for e in validate_state(state))


def test_experiment_referencing_known_hypothesis_is_fine(state):
    state["hypotheses"] = [HYPOTHESIS]
    state["experiments"] = [{"id": "E1", "hypothesis_id": "H1"}]
    assert validate_state(state) == []


@pytest.mark.parametrize("risk", ["critical", "HIGH", "", None, 3])
def test_hypothesis_risk_must_be_in_the_enum(state, risk):
    state["hypotheses"] = [{**HYPOTHESIS, "risk": risk}]
    assert any("risk must be" in e or "risk is required" in e for e in validate_state(state))


@pytest.mark.parametrize("field", ["statement", "test", "success_metric"])
def test_hypothesis_required_fields(state, field):
    state["hypotheses"] = [{**HYPOTHESIS, field: None}]
    assert any(f"hypotheses[0].{field} is required" in e for e in validate_state(state))


def test_invalid_sdd_provider(state):
    state["sdd"]["provider"] = "openspec"
    assert any("invalid sdd.provider" in e for e in validate_state(state))


def test_mvp_scope_must_be_a_list(state):
    state["mvp"]["scope"] = "auth, billing"
    assert any("mvp.scope must be a list" in e for e in validate_state(state))


def test_current_gate_requirements_are_enforced(state):
    """A state parked at a gate it does not qualify for is invalid."""
    state["lifecycle"]["current_gate"] = "G8"
    errors = validate_state(state)
    assert any("current gate G8" in e for e in errors)


def test_structural_only_mode_skips_gate_requirements(state):
    """`transition` needs structural validity without the destination's rules."""
    state["lifecycle"]["current_gate"] = "G8"
    assert validate_state(state, False) == []
    assert validate_state(state, True) != []
