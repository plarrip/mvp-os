"""`mvp-os sync`: bring a project's copied files back in line with the CLI.

`init` already did this, and still does. sync exists because the verb matters:
nobody looking for how to update reads the help for a command called init, and
a tool telling you "this is outdated, run init" reads like a mistake.
"""
from __future__ import annotations

import hashlib

OLD = "# MVP-OS Methodology\n\nAn earlier edition.\n"


def _make_stale(project):
    (project / ".mvp-os" / "methodology.md").write_text(OLD)
    (project / ".mvp-os" / ".methodology.sha256").write_text(
        hashlib.sha256(OLD.encode("utf-8")).hexdigest()
    )


def test_sync_updates_a_stale_methodology(project, run_cli):
    _make_stale(project)
    result = run_cli("sync")
    assert result.returncode == 0
    assert "Updated .mvp-os/methodology.md" in result.stdout
    assert "An earlier edition" not in (project / ".mvp-os" / "methodology.md").read_text()


def test_sync_reports_the_version_it_synced_to(project, run_cli):
    """"Outdated" is only useful next to what it is outdated against."""
    assert "Synced with mvp-os" in run_cli("sync").stdout


def test_sync_says_so_when_there_is_nothing_to_do(project, run_cli):
    assert "Already up to date." in run_cli("sync").stdout


def test_sync_refreshes_a_stale_agents_block(project, run_cli):
    agents = project / "AGENTS.md"
    agents.write_text(agents.read_text().replace("mvp-os transition", "OLD INSTRUCTION"))
    result = run_cli("sync")
    assert "Refreshed the MVP-OS block" in result.stdout
    assert "OLD INSTRUCTION" not in agents.read_text()


def test_sync_keeps_a_methodology_the_project_adapted(project, run_cli):
    methodology = project / ".mvp-os" / "methodology.md"
    methodology.write_text(methodology.read_text() + "\n## House amendment\n")
    result = run_cli("sync")
    assert "House amendment" in methodology.read_text()
    assert "has local changes" in result.stdout


def test_sync_requires_an_initialized_project(tmp_path, run_cli):
    """It refreshes what init installed; with nothing installed there is no
    sensible thing to do, and silently initializing would be a surprise."""
    result = run_cli("sync")
    assert result.returncode == 1
    assert "not initialized" in result.stdout
    assert not (tmp_path / ".mvp-os").exists()


def test_sync_does_not_touch_product_state(project, run_cli):
    from conftest import advance, read_state

    advance(project, problem={"user": "Solo founder"})
    run_cli("sync")
    assert read_state(project)["problem"]["user"] == "Solo founder"
