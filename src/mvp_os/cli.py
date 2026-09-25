"""Command surface.

The CLI is deterministic infrastructure: it initializes a project, reports
state, validates it, and accepts or refuses gate transitions. It never writes
product content -- hypotheses, evidence and decisions belong to the agent.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from importlib.metadata import PackageNotFoundError, version as _package_version
from importlib.resources import files
from pathlib import Path

from .lifecycle import (
    gate_index,
    gate_lenses,
    gate_name,
    gate_requirements_satisfied,
    is_valid_gate,
    transition_allowed,
)
from .state import ProjectState, StateError, detect_spec_kit
from .validation import validate_shape, validate_state

def get_version() -> str:
    """The installed version, read from package metadata rather than restated
    here: a version constant in the source is one more thing that can disagree
    with pyproject.toml."""
    try:
        return _package_version("mvp-os")
    except PackageNotFoundError:  # running from a source tree, uninstalled
        return "unknown"


MARKER_START = "<!-- MVP-OS instructions -->"
MARKER_END = "<!-- /MVP-OS instructions -->"
LEGACY_HEADING = "# MVP-OS project instructions"

AGENT_INSTRUCTIONS = """# MVP-OS project instructions

This project uses MVP-OS as its default product-development operating system.

1. Read `.mvp-os/methodology.md` and `.mvp-os/state.yml`.
2. Work from the current gate and next action.
3. Prefer the smallest next action that can produce meaningful validated learning.
4. Do not write production code merely because an idea was mentioned.
5. Persist durable product state in `.mvp-os/state.yml`.
6. After meaningful state changes, run `mvp-os validate`.
7. To change gates, use `mvp-os transition <GATE>`; do not edit `lifecycle.current_gate` directly.
8. A transition clears `lifecycle.next_action`. Write the new one immediately: validation fails, and further transitions are refused, until it is set.
9. If evidence is insufficient, state `INSUFFICIENT EVIDENCE`, identify what is missing, and stop.
10. At G5, run `mvp-os handoff` and give its output to the SDD provider. Never duplicate that provider's primitives.

The agent owns product reasoning and content. MVP-OS owns deterministic state validation and gate transitions.
"""


def root() -> Path:
    return Path.cwd()


def write_agent_instructions(project_root: Path) -> list[str]:
    """Install or refresh the MVP-OS block in AGENTS.md, and wire up CLAUDE.md.

    The block is framework-owned and versioned with the CLI, so it has to track
    upgrades: an agent following stale instructions is worse than one following
    none. Everything outside the markers belongs to the project and survives.
    """
    notices: list[str] = []
    block = f"{MARKER_START}\n{AGENT_INSTRUCTIONS}{MARKER_END}\n"
    agents = project_root / "AGENTS.md"

    if not agents.exists():
        agents.write_text(block, encoding="utf-8")
    else:
        existing = agents.read_text(encoding="utf-8")
        start = existing.find(MARKER_START)
        # v0.6.0 wrote the block with no marker at all.
        legacy = start == -1 and LEGACY_HEADING in existing
        if legacy:
            start = existing.index(LEGACY_HEADING)

        if start == -1:
            agents.write_text(existing.rstrip() + "\n\n" + block, encoding="utf-8")
        else:
            end = existing.find(MARKER_END, start)
            tail = (
                existing[end + len(MARKER_END):].lstrip("\n") if end != -1 else ""
            )
            updated = existing[:start] + block + (tail if tail.strip() else "")
            if updated != existing:
                agents.write_text(updated, encoding="utf-8")
                notices.append(
                    "Replaced the unmarked MVP-OS block in AGENTS.md (everything "
                    "from it to the end of the file)."
                    if legacy or end == -1
                    else "Refreshed the MVP-OS block in AGENTS.md."
                )

    claude = project_root / "CLAUDE.md"
    wrapper = "@AGENTS.md\n"
    if not claude.exists():
        claude.write_text(wrapper, encoding="utf-8")
    elif "@AGENTS.md" not in claude.read_text(encoding="utf-8"):
        claude.write_text(
            claude.read_text(encoding="utf-8").rstrip() + "\n\n" + wrapper,
            encoding="utf-8",
        )
    return notices


def _packaged(name: str) -> str:
    return files("mvp_os.resources").joinpath(name).read_text(encoding="utf-8")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def install_methodology(directory: Path) -> list[str]:
    """Install or upgrade methodology.md, conffile-style.

    Preserving local edits and propagating upstream changes are the same axis.
    "Differs from the packaged version" alone cannot tell a project's adaptation
    from a copy that is merely old, so treating both as untouchable freezes every
    project on whatever methodology it first installed.

    Recording the digest of what was installed makes the distinction: unchanged
    since install means safe to upgrade, anything else stays and is reported.
    """
    packaged = _packaged("methodology.md")
    target = directory / "methodology.md"
    stamp = directory / ".methodology.sha256"

    if not target.exists():
        target.write_text(packaged, encoding="utf-8")
        stamp.write_text(_digest(packaged), encoding="utf-8")
        return []

    current = target.read_text(encoding="utf-8")
    if current == packaged:
        stamp.write_text(_digest(packaged), encoding="utf-8")
        return []

    recorded = stamp.read_text(encoding="utf-8").strip() if stamp.exists() else None
    if recorded == _digest(current):
        target.write_text(packaged, encoding="utf-8")
        stamp.write_text(_digest(packaged), encoding="utf-8")
        return ["Updated .mvp-os/methodology.md to the packaged version."]
    if recorded is None:
        return [
            "Kept .mvp-os/methodology.md: it predates version tracking, so local "
            "edits cannot be ruled out. Delete it and re-run init to take the "
            "packaged one."
        ]
    return [
        "Kept .mvp-os/methodology.md: it has local changes. Delete it and re-run "
        "init to take the packaged one."
    ]


def methodology_is_outdated(project_root: Path) -> bool:
    """Whether the project's methodology is simply old, rather than adapted.

    Installed files only sync during `init`, so a long-running project can sit
    on a methodology several versions behind the CLI enforcing it -- and that
    file is what the agent reads every session. The recorded digest is what
    separates "outdated" from "deliberately different": if the project changed
    it, being out of step is its own decision and not worth mentioning.
    """
    directory = project_root / ".mvp-os"
    target, stamp = directory / "methodology.md", directory / ".methodology.sha256"
    if not target.is_file() or not stamp.is_file():
        return False
    current = target.read_text(encoding="utf-8")
    if current == _packaged("methodology.md"):
        return False
    return stamp.read_text(encoding="utf-8").strip() == _digest(current)


def install_resources(project_root: Path) -> list[str]:
    directory = project_root / ".mvp-os"
    directory.mkdir(parents=True, exist_ok=True)
    notices = install_methodology(directory)

    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(_packaged("gitignore.template"), encoding="utf-8")
    else:
        existing = gitignore.read_text(encoding="utf-8")
        if ".venv/" not in existing:
            gitignore.write_text(existing.rstrip() + "\n.venv/\n", encoding="utf-8")
    return notices


def plan_removal(project_root: Path) -> list[tuple[str, str]]:
    """Work out exactly how to undo `init`, without touching anything.

    Everything MVP-OS writes is either a file it owns outright or a delimited
    region inside a file the project owns. Removal has to respect that line: a
    file it created is deleted, a region it added is cut out, and anything it
    cannot prove it authored is left alone and reported.
    """
    steps: list[tuple[str, str]] = []

    if (project_root / ".mvp-os").exists():
        steps.append((".mvp-os/", "delete directory (state, methodology, digest)"))

    agents = project_root / "AGENTS.md"
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        start, end = text.find(MARKER_START), text.find(MARKER_END)
        if start != -1 and end != -1:
            remaining = text[:start] + text[end + len(MARKER_END):]
            steps.append((
                "AGENTS.md",
                "delete file (contains nothing else)" if not remaining.strip()
                else "remove the MVP-OS block, keep the rest",
            ))
        elif LEGACY_HEADING in text:
            remaining = text[: text.index(LEGACY_HEADING)]
            steps.append((
                "AGENTS.md",
                "delete file (contains nothing else)" if not remaining.strip()
                else "remove the unmarked MVP-OS block to the end of the file",
            ))

    claude = project_root / "CLAUDE.md"
    if claude.exists():
        lines = claude.read_text(encoding="utf-8").splitlines()
        if any(line.strip() == "@AGENTS.md" for line in lines):
            remaining = [line for line in lines if line.strip() != "@AGENTS.md"]
            steps.append((
                "CLAUDE.md",
                "delete file (contains nothing else)" if not "\n".join(remaining).strip()
                else "remove the @AGENTS.md line, keep the rest",
            ))

    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if text == _packaged("gitignore.template"):
            steps.append((".gitignore", "delete file (created by MVP-OS, unmodified)"))
        elif ".venv/" in text:
            # Indistinguishable from a line the project would have written anyway,
            # and removing it would un-ignore a virtualenv. Not ours to take back.
            steps.append((".gitignore", "KEEP: '.venv/' is not identifiable as ours"))

    return steps


def apply_removal(project_root: Path) -> None:
    directory = project_root / ".mvp-os"
    if directory.exists():
        shutil.rmtree(directory)

    agents = project_root / "AGENTS.md"
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        start, end = text.find(MARKER_START), text.find(MARKER_END)
        if start != -1 and end != -1:
            text = text[:start] + text[end + len(MARKER_END):]
        elif LEGACY_HEADING in text:
            text = text[: text.index(LEGACY_HEADING)]
        else:
            text = None
        if text is not None:
            _write_or_delete(agents, text)

    claude = project_root / "CLAUDE.md"
    if claude.exists():
        lines = claude.read_text(encoding="utf-8").splitlines()
        if any(line.strip() == "@AGENTS.md" for line in lines):
            kept = [line for line in lines if line.strip() != "@AGENTS.md"]
            _write_or_delete(claude, "\n".join(kept))

    gitignore = project_root / ".gitignore"
    if gitignore.exists() and gitignore.read_text(encoding="utf-8") == _packaged(
        "gitignore.template"
    ):
        gitignore.unlink()


def _write_or_delete(path: Path, text: str) -> None:
    """Write the remainder back, or delete the file if nothing of it is left."""
    if text.strip():
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
    else:
        path.unlink()


def run_remove(project_root: Path, confirmed: bool) -> int:
    steps = plan_removal(project_root)
    if not steps:
        print("Nothing to remove: no MVP-OS files found here.")
        return 0

    for target, action in steps:
        print(f"- {target}: {action}")

    if not confirmed:
        print(
            "\nNothing was removed. Re-run with --yes to apply.\n"
            "This deletes .mvp-os/state.yml, which holds the project's hypotheses, "
            "evidence and decisions."
        )
        return 0

    apply_removal(project_root)
    print("\nMVP-OS removed. Your project's own files and code are untouched.")
    print("Run `pip uninstall mvp-os` to remove the CLI itself.")
    return 0


SUMMARY_KEYS = ("statement", "observation", "summary", "description", "note", "text")


def _summary(item: dict) -> str:
    """Best available one-line description of a state entry.

    Only `id` is mandated by the schema; which field carries the meaning is the
    agent's choice, so read the likely ones and fall back to anything scalar
    rather than printing nothing.
    """
    for key in SUMMARY_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key, value in item.items():
        if key not in {"id", "hypothesis_id"} and isinstance(value, (str, int, float)):
            return str(value)
    return "(no description)"


def run_handoff(data: dict) -> int:
    """Emit the validated product context for an SDD provider to specify.

    This is the whole of the SDD boundary: MVP-OS answers what to build and why,
    and stops. It does not write specs, and it stays provider-agnostic -- the
    block is the same whoever picks it up; only the closing line differs.
    """
    lifecycle = data.get("lifecycle", {})
    gate = lifecycle.get("current_gate", "G0")
    problem = data.get("problem", {})
    hypotheses = [h for h in data.get("hypotheses", []) if isinstance(h, dict)]
    mvp = data.get("mvp", {})
    scope = mvp.get("scope") or []

    blockers = []
    if gate_index(gate) < gate_index("G5"):
        blockers.append(
            f"the project is at {gate}; a specification written before product "
            "definition is what MVP-OS exists to prevent"
        )
    if not problem.get("user"):
        blockers.append("problem.user is required")
    if not problem.get("problem"):
        blockers.append("problem.problem is required")
    if not hypotheses:
        blockers.append("at least one hypothesis is required")
    if not scope:
        blockers.append("mvp.scope must be defined")
    if blockers:
        print("REFUSED")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    supporting: dict[str, list[dict]] = {}
    for item in data.get("evidence", []):
        if isinstance(item, dict) and item.get("hypothesis_id"):
            supporting.setdefault(item["hypothesis_id"], []).append(item)

    validated = [h for h in hypotheses if supporting.get(h.get("id"))]
    open_risks = [h for h in hypotheses if not supporting.get(h.get("id"))]
    provider = data.get("sdd", {}).get("provider", "none")

    print(f"MVP-OS handoff — {gate} · SDD provider: {provider}\n")
    print("TARGET USER\n  " + problem["user"])
    print("\nPROBLEM\n  " + problem["problem"])

    if validated:
        print("\nVALIDATED HYPOTHESES")
        for h in validated:
            print(f"  {h.get('id')}  {_summary(h)}")
            if h.get("success_metric"):
                print(f"      metric: {h['success_metric']}")
            for item in supporting[h["id"]]:
                print(f"      {item.get('id')}  {_summary(item)}")

    if open_risks:
        print("\nUNVALIDATED ASSUMPTIONS — carry into the spec as risks")
        for h in open_risks:
            risk = f" (risk: {h['risk']})" if h.get("risk") else ""
            print(f"  {h.get('id')}  {_summary(h)}{risk}")

    print("\nMVP SCOPE")
    for entry in scope:
        print(f"  - {entry}")

    out_of_scope = mvp.get("out_of_scope") or []
    if out_of_scope:
        print("\nOUT OF SCOPE — do not specify")
        for entry in out_of_scope:
            print(f"  - {entry}")

    for decision in data.get("decisions", []):
        if isinstance(decision, dict):
            print(f"\nSTANDING DECISION {decision.get('id')}\n  {_summary(decision)}")

    if not validated:
        print(
            "\nNOTE: no hypothesis is backed by evidence. Everything below the "
            "problem statement is still an assumption."
        )

    print("\n" + "-" * 68)
    if provider == "spec-kit":
        print("Hand to Spec Kit:  /speckit-specify  (paste everything above this line)")
    else:
        print(
            "No SDD provider is configured. Hand the block above to whatever\n"
            "specification and implementation workflow you use."
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mvp-os")
    parser.add_argument(
        "--version", action="version", version=f"mvp-os {get_version()}"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    init = subcommands.add_parser("init")
    init.add_argument("--name")
    init.add_argument("--description")

    transition = subcommands.add_parser("transition")
    transition.add_argument("target")

    remove = subcommands.add_parser("remove")
    remove.add_argument("--yes", action="store_true")

    for command in ("status", "gate", "next", "review", "validate", "handoff"):
        subcommands.add_parser(command)
    return parser


def run_init(state: ProjectState, args: argparse.Namespace) -> int:
    provider = "spec-kit" if detect_spec_kit(root()) else "none"
    created = state.init(args.name, args.description, provider)

    changed: list[str] = []
    if not created:
        try:
            data = state.load()
        except StateError as exc:
            print(f"UNREADABLE STATE — {exc}")
            print("Fix it, or run `mvp-os remove --yes` and start over.")
            return 1
        if data.get("sdd", {}).get("provider") != provider:
            data.setdefault("sdd", {})["provider"] = provider
            changed.append(f"sdd.provider -> {provider}")
        for field, value in (("name", args.name), ("description", args.description)):
            project = data.get("project")
            if value and isinstance(project, dict) and project.get(field) != value:
                project[field] = value
                changed.append(f"project.{field} -> {value}")
        if changed:
            state.save(data)

    notices = install_resources(root()) + write_agent_instructions(root())

    print("Initialized MVP-OS" if created else "MVP-OS already initialized")
    print(f"SDD provider: {provider}")
    for change in changed:
        print(f"Updated {change}")
    for notice in notices:
        print(notice)
    return 0


def run_transition(state: ProjectState, data: dict, target: str) -> int:
    """Three checks, in order: readable state, legal move, destination satisfied."""
    target = target.upper()
    current = data.get("lifecycle", {}).get("current_gate")

    if not is_valid_gate(target):
        print(f"REJECTED\n- unknown target gate: {target}")
        return 1

    structural = validate_state(data, False)
    if structural:
        print("REJECTED")
        for error in structural:
            print(f"- invalid state: {error}")
        return 1

    status = data.get("lifecycle", {}).get("status")
    if status != "active":
        # A project that was paused or stopped is not simply idle: something was
        # decided about it. Resuming is that decision being reversed, which is
        # the agent's call to make explicitly, not a side effect of moving on.
        print(
            f"REJECTED\n- the project is {status!r}; set lifecycle.status to "
            "'active' to resume"
        )
        return 1

    if not transition_allowed(current, target):
        print(f"REJECTED\n- transition {current} → {target} is not allowed")
        return 1

    missing = gate_requirements_satisfied(data, target)
    if missing:
        print("REJECTED")
        for error in missing:
            print(f"- {error}")
        return 1

    data["lifecycle"]["current_gate"] = target
    data["lifecycle"]["next_action"] = None
    state.save(data)
    print(f"ACCEPTED\n{current} → {target} — {gate_name(target)}")
    print(
        "next_action cleared. Set it in .mvp-os/state.yml; validate will fail "
        "until you do."
    )
    return 0


def run_read(command: str, data: dict, project_root: Path) -> int:
    """status/gate/next/review. These must never crash: an agent runs them
    constantly, and a traceback is not a report."""
    shape = validate_shape(data)
    if shape:
        print("UNREADABLE STATE — .mvp-os/state.yml cannot be parsed:")
        for error in shape:
            print(f"- {error}")
        print("Fix the file, then run `mvp-os validate`.")
        return 1

    lifecycle = data.get("lifecycle", {})
    gate = lifecycle.get("current_gate", "G0")
    next_action = lifecycle.get("next_action") or "(not defined)"
    provider = data.get("sdd", {}).get("provider")

    if command == "status":
        print(
            f"Project: {data.get('project', {}).get('name') or '(unnamed)'}\n"
            f"Status: {lifecycle.get('status')}\n"
            f"Gate: {gate} — {gate_name(gate)}\n"
            f"SDD: {provider}\n"
            f"Next: {next_action}"
        )
        if methodology_is_outdated(project_root):
            print(
                f"Note: .mvp-os/methodology.md is outdated (CLI is "
                f"{get_version()}) — run `mvp-os init` to update it"
            )
    elif command == "gate":
        print(f"{gate} — {gate_name(gate)}")
        lenses = gate_lenses(gate)
        if lenses:
            print("Lenses: " + ", ".join(lenses))
    elif command == "next":
        print(lifecycle.get("next_action") or "No next action defined.")
    elif command == "review":
        print(
            f"Gate: {gate} — {gate_name(gate)}\n"
            f"Status: {lifecycle.get('status')}\n"
            f"Next action: {next_action}\n"
            f"SDD provider: {provider}\n"
            f"Hypotheses: {len(data.get('hypotheses', []))}\n"
            f"Experiments: {len(data.get('experiments', []))}\n"
            f"Evidence items: {len(data.get('evidence', []))}\n"
            f"Decisions: {len(data.get('decisions', []))}"
        )
    return 0


def main() -> int:
    args = build_parser().parse_args()
    state = ProjectState(root())

    if args.command == "init":
        return run_init(state, args)

    if args.command == "remove":
        return run_remove(root(), args.yes)

    if not state.exists():
        print("MVP-OS is not initialized. Run: mvp-os init")
        return 1

    try:
        data = state.load()
    except StateError as exc:
        print(f"UNREADABLE STATE — {exc}")
        print("Fix the file, then run `mvp-os validate`.")
        return 1

    if args.command == "validate":
        errors = validate_state(data)
        if errors:
            print("INVALID")
            for error in errors:
                print(f"- {error}")
            return 1
        print("VALID")
        return 0

    if args.command == "transition":
        return run_transition(state, data, args.target)

    if args.command == "handoff":
        if validate_shape(data):
            return run_read(args.command, data, root())
        return run_handoff(data)

    return run_read(args.command, data, root())


if __name__ == "__main__":
    raise SystemExit(main())
