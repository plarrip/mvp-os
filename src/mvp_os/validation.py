"""State validation: the deterministic checkpoint.

Two levels, deliberately separate:

- `validate_shape` asks whether the file can be read at all.
- `validate_state` adds content rules, references and the current gate's
  requirements.

The split matters because a cleared `next_action` is a normal working state
produced by every transition, while a `project` that is a string is not. Read
commands must tolerate the first and refuse the second.
"""
from __future__ import annotations

from typing import Any

from .lifecycle import gate_requirements_satisfied, is_valid_gate

REQUIRED = {
    "schema_version", "project", "lifecycle", "problem", "hypotheses",
    "experiments", "evidence", "learnings", "decisions", "mvp", "sdd",
}
ENTRY_FIELDS = ("hypotheses", "experiments", "evidence", "learnings", "decisions")
MAPPING_FIELDS = ("project", "lifecycle", "problem", "mvp", "sdd")


def validate_shape(data: Any) -> list[str]:
    """Type-level checks only: can the read commands parse this state?"""
    if not isinstance(data, dict):
        return ["state root must be a mapping"]

    errors = [f"missing top-level field: {key}" for key in sorted(REQUIRED - set(data))]
    if data.get("schema_version") != 1:
        errors.append(f"unsupported schema_version: {data.get('schema_version')!r}")
    for key in MAPPING_FIELDS:
        if not isinstance(data.get(key), dict):
            errors.append(f"{key} must be a mapping")
    for key in ENTRY_FIELDS:
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")
    return errors


def validate_state(data: Any, check_gate_requirements: bool = True) -> list[str]:
    """Full validation. `check_gate_requirements=False` skips the methodology layer,
    which is what `transition` needs: structural validity without the rules of a
    gate the project is about to leave."""
    errors = validate_shape(data)
    if not isinstance(data, dict):
        return errors

    lifecycle = data.get("lifecycle", {})
    if isinstance(lifecycle, dict):
        if not is_valid_gate(lifecycle.get("current_gate")):
            errors.append(
                f"invalid lifecycle.current_gate: {lifecycle.get('current_gate')!r}"
            )
        if lifecycle.get("status") not in {"active", "paused", "stopped", "completed"}:
            errors.append(f"invalid lifecycle.status: {lifecycle.get('status')!r}")
        # transition clears next_action; this is what makes filling it mandatory.
        if lifecycle.get("status") == "active" and not lifecycle.get("next_action"):
            errors.append(
                "lifecycle.next_action is required while the project is active"
            )

    errors.extend(_entry_errors(data))
    errors.extend(_reference_errors(data))

    sdd = data.get("sdd", {})
    if isinstance(sdd, dict):
        if sdd.get("provider") not in {"none", "spec-kit"}:
            errors.append(f"invalid sdd.provider: {sdd.get('provider')!r}")
        if sdd.get("status") not in {
            "not_started", "not_required", "active", "ready", "blocked"
        }:
            errors.append(f"invalid sdd.status: {sdd.get('status')!r}")

    mvp = data.get("mvp", {})
    if isinstance(mvp, dict):
        if not isinstance(mvp.get("scope", []), list):
            errors.append("mvp.scope must be a list")
        if not isinstance(mvp.get("out_of_scope", []), list):
            errors.append("mvp.out_of_scope must be a list")

    if (
        check_gate_requirements
        and isinstance(lifecycle, dict)
        and is_valid_gate(lifecycle.get("current_gate"))
        and lifecycle["current_gate"] != "G0"
    ):
        gate = lifecycle["current_gate"]
        errors.extend(
            f"current gate {gate}: {error}"
            for error in gate_requirements_satisfied(data, gate)
        )

    return errors


def _entry_errors(data: dict[str, Any]) -> list[str]:
    """Per-entry rules. Every entry needs an id; hypotheses need rather more."""
    errors: list[str] = []
    for field in ENTRY_FIELDS:
        if not isinstance(data.get(field), list):
            continue  # already reported by validate_shape
        for i, item in enumerate(data[field]):
            if not isinstance(item, dict):
                errors.append(f"{field}[{i}] must be a mapping")
                continue
            if not item.get("id"):
                errors.append(f"{field}[{i}].id is required")
            if field != "hypotheses":
                continue
            for required in ("statement", "risk", "test", "success_metric"):
                if not item.get(required):
                    errors.append(f"{field}[{i}].{required} is required")
            if item.get("risk") not in {"low", "medium", "high"}:
                errors.append(f"{field}[{i}].risk must be low, medium, or high")
    return errors


def _reference_errors(data: dict[str, Any]) -> list[str]:
    """Duplicate ids across all collections, and dangling hypothesis references."""
    errors: list[str] = []
    seen: set[str] = set()
    for field in ENTRY_FIELDS:
        for item in data.get(field) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            if item["id"] in seen:
                errors.append(f"duplicate id {item['id']!r}")
            seen.add(item["id"])

    hypothesis_ids = {
        item.get("id")
        for item in (data.get("hypotheses") or [])
        if isinstance(item, dict)
    }
    for i, experiment in enumerate(data.get("experiments") or []):
        if not isinstance(experiment, dict):
            continue
        reference = experiment.get("hypothesis_id")
        if reference and reference not in hypothesis_ids:
            errors.append(
                f"experiments[{i}].hypothesis_id references unknown hypothesis "
                f"{reference!r}"
            )
    return errors
