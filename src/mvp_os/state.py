"""Persistent product state: the single source of truth for a project.

Lives at `.mvp-os/state.yml`, never under an SDD provider's directory. There
are no parallel states.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

STATE_DIR = ".mvp-os"
STATE_FILE = "state.yml"

DEFAULT_STATE = {
    "schema_version": 1,
    "project": {"name": None, "description": None},
    "lifecycle": {
        "current_gate": "G0",
        "status": "active",
        "next_action": "Define the project context and initial idea.",
    },
    "problem": {"user": None, "problem": None},
    "hypotheses": [],
    "experiments": [],
    "evidence": [],
    "learnings": [],
    "decisions": [],
    "mvp": {"scope": [], "out_of_scope": []},
    "sdd": {"provider": "none", "status": "not_started"},
}


@dataclass
class ProjectState:
    """Reads and writes one project's state file."""

    root: Path

    @property
    def directory(self) -> Path:
        return self.root / STATE_DIR

    @property
    def path(self) -> Path:
        return self.directory / STATE_FILE

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> dict[str, Any]:
        return yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}

    def save(self, data: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    def init(
        self,
        name: str | None = None,
        description: str | None = None,
        provider: str = "none",
    ) -> bool:
        """Create the state file. Returns False if the project already has one."""
        if self.exists():
            return False
        data = copy.deepcopy(DEFAULT_STATE)
        data["project"]["name"] = name
        data["project"]["description"] = description
        data["sdd"]["provider"] = provider
        self.save(data)
        return True


def detect_spec_kit(root: Path) -> bool:
    """Whether Spec Kit is present. Detection only -- the core never requires it."""
    return (root / ".specify").exists() or (root / "specify.yml").exists()
