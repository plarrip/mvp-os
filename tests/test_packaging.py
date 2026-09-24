"""Packaging guards.

v0.6.0 shipped without methodology.md; v0.7.0 shipped without
gitignore.template. Both were the same defect: code referenced a resource
that packaging did not guarantee. These tests close that class.
"""
from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 / 3.10
    tomllib = None

import pytest

from conftest import REPO_ROOT, SRC

RESOURCES = SRC / "mvp_os" / "resources"


def declared_globs() -> list[str]:
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return config["tool"]["setuptools"]["package-data"]["mvp_os"]


def resource_files() -> list[Path]:
    return sorted(
        p for p in RESOURCES.iterdir() if p.is_file() and p.name != "__init__.py"
    )


@pytest.mark.skipif(tomllib is None, reason="needs tomllib (Python 3.11+)")
def test_every_resource_is_covered_by_package_data():
    """Fast, offline backstop: no resource may fall outside the declared globs.

    Fails the moment someone adds resources/foo.json without touching
    pyproject.toml -- which is exactly how `mvp-os init` got broken.
    """
    globs = declared_globs()
    uncovered = [
        p.name
        for p in resource_files()
        if not any(fnmatch.fnmatch(f"resources/{p.name}", g) for g in globs)
    ]
    assert not uncovered, (
        f"resources not matched by package-data {globs}: {uncovered}. "
        "They will be missing from any built distribution."
    )


def test_resources_referenced_in_code_exist_on_disk():
    """Every resources/<name> named in cli.py must actually exist."""
    source = (SRC / "mvp_os" / "cli.py").read_text()
    on_disk = {p.name for p in RESOURCES.iterdir()}
    for name in ("methodology.md", "gitignore.template"):
        if name in source:
            assert name in on_disk, f"cli.py reads {name} but it is not in resources/"


@pytest.mark.integration
def test_real_install_ships_every_resource(installed_env):
    """The artifact test: build + install for real, then compare file lists."""
    installed = installed_env["site_packages"] / "mvp_os" / "resources"
    missing = [
        p.name for p in resource_files() if not (installed / p.name).is_file()
    ]
    assert not missing, f"missing from the installed package: {missing}"


@pytest.mark.integration
def test_A_init_on_a_clean_repo(installed_env, tmp_path):
    """Test A from the project brief: `pip install .` then `mvp-os init`."""
    result = subprocess.run(
        [str(installed_env["bin"]), "init"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for expected in (
        ".mvp-os/state.yml",
        ".mvp-os/methodology.md",
        "AGENTS.md",
        "CLAUDE.md",
    ):
        assert (tmp_path / expected).is_file(), f"{expected} was not created"


@pytest.mark.integration
def test_agent_discovery_chain_is_wired(installed_env, tmp_path):
    """CLAUDE.md -> AGENTS.md -> methodology.md + state.yml (brief section 12)."""
    subprocess.run(
        [str(installed_env["bin"]), "init"], cwd=str(tmp_path), check=True,
        capture_output=True,
    )
    assert "@AGENTS.md" in (tmp_path / "CLAUDE.md").read_text()
    agents = (tmp_path / "AGENTS.md").read_text()
    assert ".mvp-os/methodology.md" in agents
    assert ".mvp-os/state.yml" in agents
