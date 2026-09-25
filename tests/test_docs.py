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


def test_readme_is_precise_about_what_the_integration_does():
    """v0.7.0's manifests claimed five commands that had been deleted. The
    README may describe the handoff, and must not imply more than that."""
    lowered = README.lower()
    assert "mvp-os handoff" in lowered
    assert "installs nothing" in lowered


def test_the_agent_is_not_told_how_to_uninstall():
    """`remove` is deliberately absent from AGENTS.md.

    Those instructions are the agent's standing orders, and deleting the
    project's hypotheses, evidence and decisions is never a step towards
    validated learning. Removal is a decision for the person, taken at a
    terminal, with --yes typed out.
    """
    assert "remove" not in AGENT_INSTRUCTIONS


def _lens_row(gate: str) -> str:
    """The gate's row in the Lenses table.

    Scoped to that section on purpose: the requirements table also has a row per
    gate, and matching the first one would compare against the wrong table.
    """
    section = METHODOLOGY[METHODOLOGY.index("## Lenses"):]
    section = section[: section.index("## Decisions")]
    for line in section.splitlines():
        if line.startswith(f"| {gate} "):
            return line
    raise AssertionError(f"{gate} has no row in the Lenses table")


def test_every_gate_lists_its_lenses_in_the_methodology():
    """The agent reads the methodology, not lifecycle.py. If the table drifts,
    it reasons through the wrong roles and nothing reports it."""
    from mvp_os.lifecycle import GATE_LENSES

    for gate, lenses in GATE_LENSES.items():
        row = _lens_row(gate)
        for lens in lenses:
            assert lens in row, f"{gate} calls for '{lens}', absent from its row"


def test_no_lens_is_documented_that_the_code_does_not_know():
    from mvp_os.lifecycle import GATE_LENSES, LENSES

    used = {lens for lenses in GATE_LENSES.values() for lens in lenses}
    assert used <= set(LENSES), f"undefined lenses in use: {used - set(LENSES)}"


def test_lean_is_present_at_every_gate():
    """Drop it anywhere and the process drifts towards building well rather
    than learning fast -- which is the failure the whole method exists for."""
    from mvp_os.lifecycle import GATE_LENSES

    for gate, lenses in GATE_LENSES.items():
        assert "lean" in lenses, f"{gate} has no lean lens"


def test_lenses_are_advisory_and_never_enforced():
    """A lens is a way of reasoning. Requiring one would mean validating that
    someone thought a certain way, which no tool can do.

    Checks the word 'lens' rather than each lens name: several of those names
    are ordinary words that legitimately appear in requirement messages, such
    as "at least one validation experiment is required".
    """
    import copy

    from mvp_os.lifecycle import gate_requirements_satisfied
    from mvp_os.state import DEFAULT_STATE

    state = copy.deepcopy(DEFAULT_STATE)
    for gate in GATES:
        reported = " ".join(gate_requirements_satisfied(state, gate)).lower()
        assert "lens" not in reported, f"{gate} turns a lens into a requirement"


def test_the_gate_requirement_fields_are_documented():
    """The requirements table was only ever verified by eye."""
    for field in (
        "project.description", "problem.user", "problem.problem",
        "success_metric", "mvp.scope", "not_required",
    ):
        assert field in METHODOLOGY, f"{field} is enforced but undocumented"


def test_the_decision_panel_is_documented():
    lowered = METHODOLOGY.lower()
    for pass_name in ("optimistic", "skeptical", "judgement"):
        assert pass_name in lowered
