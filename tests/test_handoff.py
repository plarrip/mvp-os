"""`mvp-os handoff`: where MVP-OS stops and an SDD provider starts.

MVP-OS answers what to build and why. The handoff is that answer, formatted for
whoever specifies it -- and nothing more. No specs, no templates, no provider
machinery.
"""
from __future__ import annotations

import pytest

from conftest import advance

HYPOTHESES = [
    {
        "id": "H1",
        "statement": "A solo founder would pay for process structure",
        "risk": "high",
        "test": "20 problem interviews",
        "success_metric": ">=8 of 20 name it unprompted",
    },
    {
        "id": "H2",
        "statement": "Teams would adopt it alongside an existing process",
        "risk": "medium",
        "test": "5 team interviews",
        "success_metric": ">=3 of 5 see a fit",
    },
]


@pytest.fixture
def at_g5(project):
    """A project with everything a specification needs."""
    advance(
        project,
        lifecycle={"current_gate": "G5", "next_action": "Specify the tracker"},
        problem={
            "user": "Solo technical founder",
            "problem": "Jumps from idea to code without validating",
        },
        hypotheses=HYPOTHESES,
        evidence=[
            {"id": "EV1", "hypothesis_id": "H1", "observation": "9 of 20 named it"}
        ],
        mvp={"scope": ["single-hypothesis tracker"], "out_of_scope": ["multi-user"]},
        sdd={"provider": "none", "status": "not_required"},
    )
    return project


def test_handoff_refuses_before_product_definition(project, run_cli):
    """The core promise: no specification before the product is defined."""
    result = run_cli("handoff")
    assert result.returncode == 1
    assert "REFUSED" in result.stdout
    assert "the project is at G0" in result.stdout


@pytest.mark.parametrize(
    "missing,expected",
    [
        ({"problem": {"user": None}}, "problem.user is required"),
        ({"problem": {"problem": None}}, "problem.problem is required"),
        ({"hypotheses": []}, "at least one hypothesis is required"),
        ({"mvp": {"scope": []}}, "mvp.scope must be defined"),
    ],
)
def test_handoff_refuses_an_incomplete_product_context(at_g5, run_cli, missing, expected):
    advance(at_g5, **missing)
    result = run_cli("handoff")
    assert result.returncode == 1
    assert expected in result.stdout


def test_handoff_emits_the_product_context(at_g5, run_cli):
    result = run_cli("handoff")
    assert result.returncode == 0
    for expected in (
        "Solo technical founder",
        "Jumps from idea to code without validating",
        "single-hypothesis tracker",
    ):
        assert expected in result.stdout


def test_evidence_is_attached_to_the_hypothesis_it_supports(at_g5, run_cli):
    output = run_cli("handoff").stdout
    validated = output.index("VALIDATED HYPOTHESES")
    unvalidated = output.index("UNVALIDATED ASSUMPTIONS")
    assert "EV1" in output[validated:unvalidated]
    assert "H1" in output[validated:unvalidated]


def test_hypotheses_without_evidence_are_flagged_as_risks(at_g5, run_cli):
    """A spec that cannot tell findings from assumptions will treat both as fact."""
    output = run_cli("handoff").stdout
    risks = output[output.index("UNVALIDATED ASSUMPTIONS"):]
    assert "H2" in risks
    assert "risk: medium" in risks


def test_out_of_scope_is_carried_across(at_g5, run_cli):
    """The most expensive thing to lose in a handoff: what was ruled out."""
    output = run_cli("handoff").stdout
    assert "OUT OF SCOPE" in output
    assert "multi-user" in output


def test_a_context_with_no_evidence_at_all_says_so(at_g5, run_cli):
    advance(at_g5, evidence=[])
    output = run_cli("handoff").stdout
    assert "no hypothesis is backed by evidence" in output
    assert "still an assumption" in output


def test_decisions_travel_with_the_context(at_g5, run_cli):
    advance(at_g5, decisions=[{"id": "D1", "summary": "Solo founder only for now"}])
    output = run_cli("handoff").stdout
    assert "STANDING DECISION D1" in output
    assert "Solo founder only for now" in output


def test_the_closing_line_names_spec_kit_when_it_is_the_provider(at_g5, run_cli):
    advance(at_g5, sdd={"provider": "spec-kit", "status": "ready"})
    output = run_cli("handoff").stdout
    assert "/speckit-specify" in output


def test_standalone_keeps_the_handoff_provider_agnostic(at_g5, run_cli):
    """The core must not become a Spec Kit wrapper: the block is the same
    whoever picks it up, and only the closing line differs."""
    output = run_cli("handoff").stdout
    assert "speckit" not in output.lower()
    assert "No SDD provider is configured" in output


def test_handoff_tolerates_entries_whose_fields_it_does_not_know(at_g5, run_cli):
    """Only `id` is mandated; the agent chooses what else an entry carries."""
    advance(at_g5, evidence=[{"id": "EV9", "hypothesis_id": "H1", "finding": "odd key"}])
    output = run_cli("handoff").stdout
    assert "EV9" in output
    assert "odd key" in output


def test_handoff_reports_an_unreadable_state(at_g5, run_cli):
    (at_g5 / ".mvp-os" / "state.yml").write_text("project: [broken\n")
    result = run_cli("handoff")
    assert result.returncode == 1
    assert "UNREADABLE STATE" in result.stdout
    assert "Traceback" not in result.stderr
