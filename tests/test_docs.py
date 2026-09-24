"""Guards against documentation drifting away from behaviour.

The packaged methodology is not decoration: it is what the agent reads at the
start of every session. When it disagrees with the code, the agent follows the
wrong contract -- which is a functional bug, not a cosmetic one.
"""
from __future__ import annotations

from importlib.resources import files

from conftest import REPO_ROOT
from mvp_os.cli import AGENT_INSTRUCTIONS
from mvp_os.lifecycle import GATES

METHODOLOGY = files("mvp_os.resources").joinpath("methodology.md").read_text()
README = (REPO_ROOT / "README.md").read_text()
COMMANDS = (
    "init", "status", "gate", "next", "review", "validate", "transition", "remove",
)


def test_methodology_documents_every_gate():
    for gate, name in GATES.items():
        assert gate in METHODOLOGY, f"{gate} is not documented"
        assert name in METHODOLOGY, f"{gate} ({name}) has no name in the methodology"


def test_the_three_levels_do_not_restate_each_other():
    """AGENTS.md carries the mechanics; the methodology carries the method.

    Both are read every session, so duplication costs context on every run and
    creates two places to update when a rule changes. The division is the
    project's own: instructions say how to behave, the methodology says what
    MVP-OS is and why.
    """
    for mechanic in ("mvp-os transition", "mvp-os validate", "current_gate"):
        assert mechanic in AGENT_INSTRUCTIONS, f"{mechanic} must be an instruction"
        assert mechanic not in METHODOLOGY, (
            f"{mechanic} is an operating instruction, already in AGENTS.md"
        )


def test_methodology_states_the_lifecycle_is_not_linear():
    assert "graph" in METHODOLOGY
    assert "G3 → G2" in METHODOLOGY


def test_agent_instructions_point_at_the_other_two_levels():
    """AGENTS.md must delegate, not restate the methodology (brief section 13)."""
    assert ".mvp-os/methodology.md" in AGENT_INSTRUCTIONS
    assert ".mvp-os/state.yml" in AGENT_INSTRUCTIONS
    assert "mvp-os transition" in AGENT_INSTRUCTIONS
    assert "next_action" in AGENT_INSTRUCTIONS
    assert len(AGENT_INSTRUCTIONS.splitlines()) < 30, (
        "AGENTS.md is restating the methodology instead of pointing at it"
    )


def test_readme_documents_every_command():
    for command in COMMANDS:
        assert f"mvp-os {command}" in README or f"`{command}`" in README, (
            f"{command} is undocumented in the README"
        )


def test_readme_does_not_claim_a_working_spec_kit_integration():
    """It is detected, not integrated. Saying otherwise is how v0.7.0 misled."""
    lowered = README.lower()
    assert "not finished" in lowered or "not implemented" in lowered


def test_the_agent_is_not_told_how_to_uninstall():
    """`remove` is deliberately absent from AGENTS.md.

    Those instructions are the agent's standing orders, and deleting the
    project's hypotheses, evidence and decisions is never a step towards
    validated learning. Removal is a decision for the person, taken at a
    terminal, with --yes typed out.
    """
    assert "remove" not in AGENT_INSTRUCTIONS
