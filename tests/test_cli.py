"""CLI behaviour, driven the way an agent drives it: one subprocess at a time."""
from __future__ import annotations

import pytest

from conftest import HYPOTHESIS_FIXTURE, advance, read_state


def test_init_creates_the_four_discovery_files(project):
    for expected in (
        ".mvp-os/state.yml",
        ".mvp-os/methodology.md",
        "AGENTS.md",
        "CLAUDE.md",
    ):
        assert (project / expected).is_file()


def test_init_is_idempotent(project, run_cli):
    """Re-running init must not duplicate the instruction block."""
    before = (project / "AGENTS.md").read_text()
    result = run_cli("init")
    assert result.returncode == 0
    assert "already initialized" in result.stdout
    after = (project / "AGENTS.md").read_text()
    assert after == before
    assert after.count("# MVP-OS project instructions") == 1


def test_init_appends_to_an_existing_agents_file(tmp_path, run_cli):
    """Existing agent instructions must survive (brief section 18)."""
    (tmp_path / "AGENTS.md").write_text("# House rules\n\nAlways run the linter.\n")
    run_cli("init")
    content = (tmp_path / "AGENTS.md").read_text()
    assert "Always run the linter." in content
    assert "MVP-OS project instructions" in content


def test_init_preserves_an_existing_claude_file(tmp_path, run_cli):
    (tmp_path / "CLAUDE.md").write_text("# Notes\n\nUse pnpm.\n")
    run_cli("init")
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "Use pnpm." in content
    assert "@AGENTS.md" in content


def test_commands_fail_cleanly_before_init(tmp_path, run_cli):
    for command in ("status", "gate", "next", "review", "validate"):
        result = run_cli(command)
        assert result.returncode == 1
        assert "not initialized" in result.stdout
        assert "Traceback" not in result.stderr


def test_read_commands_work_on_a_fresh_project(project, run_cli):
    assert "G0 — Intake" in run_cli("gate").stdout
    assert "Intake" in run_cli("status").stdout
    assert run_cli("next").stdout.strip()
    assert "Hypotheses: 0" in run_cli("review").stdout
    assert run_cli("validate").stdout.strip() == "VALID"


def test_D_and_E_full_journey(project, run_cli):
    """Tests D and E end to end: G0->G1->G2->G3, then back to G2."""
    advance(
        project,
        project={"name": "MVP-OS", "description": "Lean MVP operating system"},
        problem={"user": "Solo technical founder"},
    )
    assert "ACCEPTED" in run_cli("transition", "G1").stdout

    advance(project, problem={"problem": "Jumps from idea to code without validating"})
    assert "ACCEPTED" in run_cli("transition", "G2").stdout

    refused = run_cli("transition", "G3")
    assert refused.returncode == 1
    assert "at least one hypothesis is required" in refused.stdout

    advance(project, hypotheses=[HYPOTHESIS_FIXTURE])
    assert "ACCEPTED" in run_cli("transition", "G3").stdout
    assert read_state(project)["lifecycle"]["current_gate"] == "G3"

    # Test E: new evidence sends us back.
    back = run_cli("transition", "G2")
    assert "ACCEPTED" in back.stdout
    assert read_state(project)["lifecycle"]["current_gate"] == "G2"
    assert run_cli("validate").stdout.strip() == "VALID"


def test_C_refuses_to_skip_gates(project, run_cli):
    result = run_cli("transition", "G7")
    assert result.returncode == 1
    assert "REJECTED" in result.stdout
    assert "not allowed" in result.stdout
    assert read_state(project)["lifecycle"]["current_gate"] == "G0"


def test_transition_to_an_unknown_gate(project, run_cli):
    result = run_cli("transition", "G99")
    assert result.returncode == 1
    assert "unknown target gate" in result.stdout


def test_transition_refuses_to_move_a_structurally_broken_state(project, run_cli):
    advance(project, hypotheses=["not a mapping"])
    result = run_cli("transition", "G1")
    assert result.returncode == 1
    assert "invalid state" in result.stdout


def test_rejected_transition_leaves_the_state_untouched(project, run_cli):
    before = (project / ".mvp-os" / "state.yml").read_text()
    run_cli("transition", "G7")
    assert (project / ".mvp-os" / "state.yml").read_text() == before


def test_G_agent_edits_to_state_survive_and_validate(project, run_cli):
    """Test G: the agent owns content; the CLI must not fight it."""
    advance(
        project,
        project={"name": "MVP-OS", "description": "Lean MVP operating system"},
        evidence=[{"id": "EV1", "source": "interview", "observation": "6 of 12 improvise"}],
    )
    assert run_cli("validate").stdout.strip() == "VALID"
    assert read_state(project)["evidence"][0]["id"] == "EV1"
    assert "MVP-OS" in run_cli("status").stdout


def test_validate_reports_concrete_errors(project):
    advance(project, schema_version=99)
    # Import here so the failure surfaces as an assertion, not a collection error.
    from mvp_os.validation import validate_state

    errors = validate_state(read_state(project))
    assert any("schema_version" in e for e in errors)


# --- known defects, documented as executable specifications -------------------
# These are expected to fail today. When a fix lands, strict xfail turns the
# unexpected pass into a failure, forcing the marker to be removed.

@pytest.mark.xfail(
    strict=True,
    reason="status raises AttributeError instead of reporting a corrupt state",
)
def test_status_degrades_gracefully_on_a_corrupt_state(project, run_cli):
    advance(project, project="not a mapping")
    result = run_cli("status")
    assert "Traceback" not in result.stderr
    assert result.returncode == 1


@pytest.mark.xfail(
    strict=True,
    reason="transition overwrites next_action with boilerplate, destroying "
           "the agent's reasoning at the moment it matters most",
)
def test_transition_does_not_clobber_next_action(project, run_cli):
    advance(
        project,
        project={"description": "Lean MVP operating system"},
        problem={"user": "Solo technical founder"},
        lifecycle={"next_action": "Interview 5 founders about their current process"},
    )
    run_cli("transition", "G1")
    assert (
        read_state(project)["lifecycle"]["next_action"]
        == "Interview 5 founders about their current process"
    )


@pytest.mark.xfail(
    strict=True, reason="install_resources overwrites methodology.md silently"
)
def test_init_does_not_silently_discard_local_methodology_edits(project, run_cli):
    methodology = project / ".mvp-os" / "methodology.md"
    methodology.write_text(methodology.read_text() + "\n## House amendment\n")
    run_cli("init")
    assert "House amendment" in methodology.read_text()


@pytest.mark.xfail(
    strict=True, reason="init --name is ignored on an already-initialized project"
)
def test_init_name_on_an_existing_project_is_not_silently_dropped(project, run_cli):
    result = run_cli("init", "--name", "Renamed")
    state = read_state(project)
    assert state["project"]["name"] == "Renamed" or "Renamed" in result.stdout
