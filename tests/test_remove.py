"""`mvp-os remove`: undoing init without taking anything that is not ours."""
from __future__ import annotations

from conftest import read_state


def test_remove_without_yes_changes_nothing(project, run_cli):
    """Destructive by nature -- state.yml holds every hypothesis and decision."""
    before = sorted(p.name for p in project.iterdir())
    result = run_cli("remove")
    assert result.returncode == 0
    assert "Nothing was removed" in result.stdout
    assert ".mvp-os/" in result.stdout
    assert sorted(p.name for p in project.iterdir()) == before
    assert read_state(project)["lifecycle"]["current_gate"] == "G0"


def test_remove_lists_what_it_would_touch(project, run_cli):
    output = run_cli("remove").stdout
    for target in (".mvp-os/", "AGENTS.md", "CLAUDE.md", ".gitignore"):
        assert target in output


def test_remove_yes_deletes_everything_it_created(project, run_cli):
    result = run_cli("remove", "--yes")
    assert result.returncode == 0
    for gone in (".mvp-os", "AGENTS.md", "CLAUDE.md", ".gitignore"):
        assert not (project / gone).exists(), f"{gone} survived"
    assert "untouched" in result.stdout


def test_remove_restores_a_pre_existing_project_exactly(tmp_path, run_cli):
    """The case that matters: a repo that had its own files before MVP-OS."""
    originals = {
        "AGENTS.md": "# House rules\n\nAlways run the linter.\n",
        "CLAUDE.md": "# Project notes\n\nUse pnpm, not npm.\n",
        ".gitignore": "node_modules/\ndist/\n",
        "index.js": "console.log('hello')\n",
    }
    for name, content in originals.items():
        (tmp_path / name).write_text(content)

    run_cli("init")
    run_cli("remove", "--yes")

    for name, content in originals.items():
        if name == ".gitignore":
            continue  # .venv/ is deliberately kept, asserted separately
        assert (tmp_path / name).read_text() == content, f"{name} was not restored"
    assert not (tmp_path / ".mvp-os").exists()


def test_remove_keeps_a_gitignore_line_it_cannot_claim(tmp_path, run_cli):
    """'.venv/' in a project's own .gitignore is indistinguishable from its own."""
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    run_cli("init")
    result = run_cli("remove", "--yes")
    assert (tmp_path / ".gitignore").exists()
    assert ".venv/" in (tmp_path / ".gitignore").read_text()
    assert "KEEP" in result.stdout


def test_remove_deletes_a_gitignore_it_created_untouched(project, run_cli):
    run_cli("remove", "--yes")
    assert not (project / ".gitignore").exists()


def test_remove_keeps_a_gitignore_the_project_has_since_edited(project, run_cli):
    gitignore = project / ".gitignore"
    gitignore.write_text(gitignore.read_text() + "coverage/\n")
    run_cli("remove", "--yes")
    assert gitignore.exists()
    assert "coverage/" in gitignore.read_text()


def test_remove_handles_a_legacy_unmarked_block(tmp_path, run_cli):
    (tmp_path / "AGENTS.md").write_text(
        "# House rules\n\nAlways run the linter.\n\n"
        "# MVP-OS project instructions\n\n1. Read `.mvp-os/methodology.md`.\n"
    )
    run_cli("remove", "--yes")
    content = (tmp_path / "AGENTS.md").read_text()
    assert "Always run the linter." in content
    assert "MVP-OS" not in content


def test_remove_cleans_up_a_half_installed_project(tmp_path, run_cli):
    """A crashed init can leave .mvp-os with no instruction files -- as happened."""
    (tmp_path / ".mvp-os").mkdir()
    (tmp_path / ".mvp-os" / "state.yml").write_text("schema_version: 1\n")
    result = run_cli("remove", "--yes")
    assert result.returncode == 0
    assert not (tmp_path / ".mvp-os").exists()


def test_remove_on_a_clean_directory_says_so(tmp_path, run_cli):
    result = run_cli("remove", "--yes")
    assert result.returncode == 0
    assert "Nothing to remove" in result.stdout


def test_the_project_is_not_initialized_afterwards(project, run_cli):
    run_cli("remove", "--yes")
    result = run_cli("status")
    assert result.returncode == 1
    assert "not initialized" in result.stdout


def test_remove_leaves_project_code_alone(project, run_cli):
    (project / "src").mkdir()
    (project / "src" / "main.py").write_text("print('hello')\n")
    run_cli("remove", "--yes")
    assert (project / "src" / "main.py").read_text() == "print('hello')\n"


def test_remove_points_at_a_command_that_can_actually_work(project, run_cli):
    """It used to say `pip uninstall mvp-os`, which cannot find a tool installed
    by `uv tool` or `pipx` -- and outside a virtualenv there is often no `pip`
    on PATH at all. The README was corrected and this message was not, so a
    user still hit it. Fixing docs is not fixing the product."""
    output = run_cli("remove", "--yes").stdout
    assert "pip uninstall" not in output
    assert "uv tool uninstall" in output
    assert "pipx uninstall" in output
