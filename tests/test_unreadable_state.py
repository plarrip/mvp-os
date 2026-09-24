"""A state file that cannot be parsed at all.

The agent writes this YAML by hand, so a syntax error is the likeliest failure
in daily use -- likelier than any of the malformed-but-parseable states the
validation tests cover. Every command that reads state must answer with a
report, never a PyYAML stack trace.
"""
from __future__ import annotations

import pytest

BROKEN_YAML = "schema_version: 1\nproject: [unclosed\n"
READING_COMMANDS = ["status", "gate", "next", "review", "validate", "transition"]


@pytest.mark.parametrize("command", READING_COMMANDS)
def test_no_command_crashes_on_unparseable_yaml(project, run_cli, command):
    (project / ".mvp-os" / "state.yml").write_text(BROKEN_YAML)
    args = (command, "G1") if command == "transition" else (command,)
    result = run_cli(*args)
    assert "Traceback" not in result.stderr, f"{command} raised instead of reporting"
    assert result.returncode == 1
    assert "UNREADABLE STATE" in result.stdout


def test_the_error_says_where_the_problem_is(project, run_cli):
    """'not valid YAML' is useless on its own; the agent has to find the line."""
    (project / ".mvp-os" / "state.yml").write_text(BROKEN_YAML)
    output = run_cli("status").stdout
    assert "not valid YAML" in output
    assert "line 3" in output


def test_init_reports_an_unparseable_state_rather_than_crashing(project, run_cli):
    (project / ".mvp-os" / "state.yml").write_text(BROKEN_YAML)
    result = run_cli("init")
    assert "Traceback" not in result.stderr
    assert result.returncode == 1
    assert "UNREADABLE STATE" in result.stdout
    assert "remove --yes" in result.stdout


def test_a_state_file_that_cannot_be_opened(project, run_cli):
    """Exotic, but it took the same path to a stack trace."""
    state_file = project / ".mvp-os" / "state.yml"
    state_file.unlink()
    state_file.mkdir()
    result = run_cli("status")
    assert "Traceback" not in result.stderr
    assert result.returncode == 1
    assert "cannot read" in result.stdout


def test_remove_still_works_on_an_unparseable_state(project, run_cli):
    """The escape hatch must not depend on the thing that is broken."""
    (project / ".mvp-os" / "state.yml").write_text(BROKEN_YAML)
    result = run_cli("remove", "--yes")
    assert result.returncode == 0
    assert not (project / ".mvp-os").exists()
