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
COMMANDS = ("init", "status", "gate", "next", "review", "validate", "transition")


def test_methodology_documents_every_gate():
    for gate, name in GATES.items():
        assert gate in METHODOLOGY, f"{gate} is not documented"
        assert name in METHODOLOGY, f"{gate} ({name}) has no name in the methodology"


def test_methodology_documents_the_transition_contract():
    """An agent that does not know these rules will fight the CLI."""
    assert "mvp-os transition" in METHODOLOGY
    assert "current_gate" in METHODOLOGY
    assert "next_action" in METHODOLOGY


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
