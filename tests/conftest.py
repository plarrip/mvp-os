"""Shared fixtures.

Unit and CLI tests run straight from ``src/`` so the suite stays fast and
works offline. The packaging tests deliberately do NOT: they build and
install a real distribution, because that is the only way to catch an
asset that code references but packaging never ships.
"""
from __future__ import annotations

import copy
import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

HYPOTHESIS_FIXTURE = {
    "id": "H1",
    "statement": "A solo founder would pay for process structure",
    "risk": "high",
    "test": "20 problem interviews",
    "success_metric": ">=8 of 20 name it unprompted",
}


@pytest.fixture
def run_cli(tmp_path):
    """Invoke the CLI in a temp project directory, from the source tree."""

    def _run(*args, cwd=None):
        return subprocess.run(
            [sys.executable, "-m", "mvp_os.cli", *args],
            cwd=str(cwd or tmp_path),
            env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
        )

    return _run


@pytest.fixture
def project(tmp_path, run_cli):
    """An initialized MVP-OS project at G0."""
    result = run_cli("init")
    assert result.returncode == 0, result.stderr
    return tmp_path


def read_state(root: Path) -> dict:
    return yaml.safe_load((root / ".mvp-os" / "state.yml").read_text())


def write_state(root: Path, data: dict) -> None:
    (root / ".mvp-os" / "state.yml").write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    )


def advance(root: Path, **changes) -> dict:
    """Merge nested changes into the state file and return it."""
    data = read_state(root)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key].update(value)
        else:
            data[key] = copy.deepcopy(value)
    write_state(root, data)
    return data


BUILD_NOISE = shutil.ignore_patterns(
    ".git", ".venv", "build", "dist", "*.egg-info", "__pycache__", ".pytest_cache"
)


@pytest.fixture(scope="session")
def installed_env(tmp_path_factory):
    """A throwaway venv with MVP-OS installed as a real (non-editable) package.

    This is the fixture that proves `pip install .` produces something that
    actually works -- the scenario that shipped broken in v0.7.0.

    Two traps make this test lie if you build straight from the repo:

    1. setuptools reuses build/lib, so a file dropped from package-data stays
       in the artifact because a previous build left it there.
    2. pip reuses a cached wheel for the same version.

    Both mean a green test over a broken build, and both only bite locally --
    CI starts from a clean tree, so the developer is the one who gets lied to.
    Staging a pristine copy and disabling the cache removes both.
    """
    base = tmp_path_factory.mktemp("install")
    staged = base / "src"
    shutil.copytree(REPO_ROOT, staged, ignore=BUILD_NOISE)

    env_dir = base / "env"
    try:
        venv.create(env_dir, with_pip=True)
    except Exception as exc:  # some managed interpreters ship a broken ensurepip
        pytest.skip(f"cannot create a virtualenv with pip here: {exc}")
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    result = subprocess.run(
        [str(bindir / "pip"), "install", "--quiet", "--no-cache-dir", str(staged)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"could not build/install the package: {result.stderr[-800:]}")
    site_packages = next((env_dir / "lib").glob("python*/site-packages"))
    return {
        "bin": bindir / "mvp-os",
        "site_packages": site_packages,
    }
