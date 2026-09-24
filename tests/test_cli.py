"""CLI behaviour, driven the way an agent drives it: one subprocess at a time."""
from __future__ import annotations

import pytest

import hashlib

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


def test_the_block_is_delimited_at_both_ends(project):
    agents = (project / "AGENTS.md").read_text()
    assert agents.count("<!-- MVP-OS instructions -->") == 1
    assert agents.count("<!-- /MVP-OS instructions -->") == 1


def test_init_refreshes_a_stale_block_instead_of_freezing_it(project, run_cli):
    """The block is versioned with the CLI; it has to track upgrades.

    An agent following stale instructions is worse than one following none.
    """
    agents = project / "AGENTS.md"
    stale = agents.read_text().replace(
        "To change gates, use `mvp-os transition <GATE>`", "OLD INSTRUCTION"
    )
    agents.write_text(stale)
    result = run_cli("init")
    refreshed = agents.read_text()
    assert "OLD INSTRUCTION" not in refreshed
    assert "mvp-os transition" in refreshed
    assert "Refreshed the MVP-OS block" in result.stdout


def test_refreshing_preserves_project_content_around_the_block(project, run_cli):
    agents = project / "AGENTS.md"
    agents.write_text(
        "# House rules\n\nAlways run the linter.\n\n"
        + agents.read_text()
        + "\n## Deployment\n\nShip on Fridays, we are brave.\n"
    )
    run_cli("init")
    content = agents.read_text()
    assert "Always run the linter." in content
    assert "Ship on Fridays, we are brave." in content
    assert content.count("<!-- MVP-OS instructions -->") == 1


def test_a_legacy_unmarked_block_is_replaced_not_duplicated(tmp_path, run_cli):
    """v0.6.0 wrote the block without any marker, so re-init appended a copy."""
    (tmp_path / "AGENTS.md").write_text(
        "# House rules\n\nAlways run the linter.\n\n"
        "# MVP-OS project instructions\n\n1. Read `.mvp-os/methodology.md`.\n"
    )
    result = run_cli("init")
    content = (tmp_path / "AGENTS.md").read_text()
    assert content.count("# MVP-OS project instructions") == 1
    assert "Always run the linter." in content
    assert "Replaced the unmarked MVP-OS block" in result.stdout


def test_a_current_block_is_left_alone_silently(project, run_cli):
    before = (project / "AGENTS.md").read_text()
    result = run_cli("init")
    assert (project / "AGENTS.md").read_text() == before
    assert "AGENTS.md" not in result.stdout


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
    """Tests D and E end to end: G0->G1->G2->G3, then back to G2.

    Note the plan/move rhythm. Because a transition clears next_action and
    transitions structurally validate first, the agent cannot climb two gates
    without saying what it intends to do at each one. Declaring intent is the
    price of moving.
    """
    advance(
        project,
        project={"name": "MVP-OS", "description": "Lean MVP operating system"},
        problem={"user": "Solo technical founder"},
    )
    assert "ACCEPTED" in run_cli("transition", "G1").stdout

    advance(
        project,
        problem={"problem": "Jumps from idea to code without validating"},
        lifecycle={"next_action": "Name the riskiest assumption"},
    )
    assert "ACCEPTED" in run_cli("transition", "G2").stdout

    advance(project, lifecycle={"next_action": "Write H1 with a success metric"})
    refused = run_cli("transition", "G3")
    assert refused.returncode == 1
    assert "at least one hypothesis is required" in refused.stdout

    advance(project, hypotheses=[HYPOTHESIS_FIXTURE])
    assert "ACCEPTED" in run_cli("transition", "G3").stdout
    assert read_state(project)["lifecycle"]["current_gate"] == "G3"

    # Test E: new evidence sends us back.
    advance(project, lifecycle={"next_action": "H1 refuted; revisit the segment"})
    back = run_cli("transition", "G2")
    assert "ACCEPTED" in back.stdout
    assert read_state(project)["lifecycle"]["current_gate"] == "G2"

    # Every transition leaves next_action empty on purpose; the agent fills it.
    assert read_state(project)["lifecycle"]["next_action"] is None
    advance(project, lifecycle={"next_action": "Reframe H1 around the new segment"})
    assert run_cli("validate").stdout.strip() == "VALID"


def test_transitions_cannot_be_chained_without_declaring_intent(project, run_cli):
    """Consequence of the cleared hole: no silent gate climbing."""
    advance(
        project,
        project={"description": "Lean MVP operating system"},
        problem={"user": "Solo founder", "problem": "Builds before validating"},
    )
    assert "ACCEPTED" in run_cli("transition", "G1").stdout
    blocked = run_cli("transition", "G2")
    assert blocked.returncode == 1
    assert "next_action is required" in blocked.stdout
    assert read_state(project)["lifecycle"]["current_gate"] == "G1"


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

@pytest.mark.parametrize("command", ["status", "gate", "next", "review"])
def test_read_commands_refuse_an_unreadable_state_without_crashing(
    project, run_cli, command
):
    """An agent runs these constantly; a Python traceback is not a report."""
    advance(project, project="not a mapping")
    result = run_cli(command)
    assert "Traceback" not in result.stderr
    assert result.returncode == 1
    assert "UNREADABLE STATE" in result.stdout
    assert "project must be a mapping" in result.stdout


def test_read_commands_still_work_on_an_incomplete_state(project, run_cli):
    """A cleared next_action is a normal working state, not an unreadable one.

    Shape and completeness are different failures: one means the file cannot
    be parsed, the other means the agent has not finished thinking yet.
    """
    advance(
        project,
        project={"description": "Lean MVP operating system"},
        problem={"user": "Solo technical founder"},
    )
    run_cli("transition", "G1")
    result = run_cli("status")
    assert result.returncode == 0
    assert "G1" in result.stdout
    assert "(not defined)" in result.stdout
    assert run_cli("validate").returncode == 1


def test_transition_clears_next_action_instead_of_inventing_one(project, run_cli):
    """A gate change invalidates the old plan; the CLI must not write the new one.

    Section 10: MVP-OS validates, the agent reasons. Leaving a mandatory hole
    forces the agent to state where it is going; filling it with boilerplate
    would overwrite real reasoning at exactly the moment a transition carries
    the most information -- above all on a backward move, which happens
    precisely because evidence invalidated something.
    """
    advance(
        project,
        project={"description": "Lean MVP operating system"},
        problem={"user": "Solo technical founder"},
        lifecycle={"next_action": "Interview 5 founders about their process"},
    )
    result = run_cli("transition", "G1")
    assert "ACCEPTED" in result.stdout
    assert "next_action cleared" in result.stdout
    assert read_state(project)["lifecycle"]["next_action"] is None


def test_validate_fails_until_the_agent_states_the_next_action(project, run_cli):
    """The hole is mandatory, not cosmetic."""
    advance(
        project,
        project={"description": "Lean MVP operating system"},
        problem={"user": "Solo technical founder"},
    )
    run_cli("transition", "G1")
    failed = run_cli("validate")
    assert failed.returncode == 1
    assert "next_action is required" in failed.stdout

    advance(project, lifecycle={"next_action": "Draft the riskiest assumption"})
    assert run_cli("validate").stdout.strip() == "VALID"


def test_init_does_not_silently_discard_local_methodology_edits(project, run_cli):
    """Re-running init must not destroy a project's adapted methodology."""
    methodology = project / ".mvp-os" / "methodology.md"
    methodology.write_text(methodology.read_text() + "\n## House amendment\n")
    result = run_cli("init")
    assert "House amendment" in methodology.read_text()
    assert "has local changes" in result.stdout


def test_init_records_what_it_installed(project):
    stamp = project / ".mvp-os" / ".methodology.sha256"
    assert stamp.is_file()
    methodology = (project / ".mvp-os" / "methodology.md").read_text()
    assert stamp.read_text().strip() == hashlib.sha256(
        methodology.encode("utf-8")
    ).hexdigest()


def test_init_upgrades_an_untouched_but_outdated_methodology(project, run_cli):
    """Keeping local edits must not mean nobody ever receives an update.

    The recorded digest is what separates "the project adapted this" from
    "this is simply old" -- without it both look identical and every project
    freezes on the methodology it first installed.
    """
    methodology = project / ".mvp-os" / "methodology.md"
    packaged = methodology.read_text()
    outdated = "# MVP-OS Methodology\n\nAn older edition.\n"
    methodology.write_text(outdated)
    (project / ".mvp-os" / ".methodology.sha256").write_text(
        hashlib.sha256(outdated.encode("utf-8")).hexdigest()
    )

    result = run_cli("init")
    assert methodology.read_text() == packaged
    assert "Updated .mvp-os/methodology.md" in result.stdout


def test_init_keeps_a_methodology_it_cannot_vouch_for(project, run_cli):
    """No recorded digest means edits cannot be ruled out, so keep the file."""
    methodology = project / ".mvp-os" / "methodology.md"
    (project / ".mvp-os" / ".methodology.sha256").unlink()
    methodology.write_text("# MVP-OS Methodology\n\nAn older edition.\n")
    result = run_cli("init")
    assert "An older edition." in methodology.read_text()
    assert "predates version tracking" in result.stdout


def test_an_up_to_date_methodology_produces_no_noise(project, run_cli):
    result = run_cli("init")
    assert "methodology" not in result.stdout


def test_init_reinstalls_a_deleted_methodology(project, run_cli):
    """Keeping local edits must not mean the file can never be restored."""
    methodology = project / ".mvp-os" / "methodology.md"
    methodology.unlink()
    run_cli("init")
    assert methodology.is_file()
    assert methodology.read_text().strip()


def test_init_name_on_an_existing_project_is_applied(project, run_cli):
    result = run_cli("init", "--name", "Renamed", "--description", "A lean thing")
    state = read_state(project)
    assert state["project"]["name"] == "Renamed"
    assert state["project"]["description"] == "A lean thing"
    assert "project.name -> Renamed" in result.stdout


def test_init_without_arguments_reports_no_changes(project, run_cli):
    result = run_cli("init")
    assert "Updated" not in result.stdout
