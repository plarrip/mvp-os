# Testing MVP-OS

## Automated suite

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

Unit and CLI tests run straight from `src/` and need no install. Tests marked
`integration` build and install a real distribution into a throwaway venv:

```bash
pytest -m integration        # only those
pytest -m "not integration"  # skip them (fast, fully offline)
```

The integration fixture stages a pristine copy of the repository before
building. This is deliberate: setuptools reuses `build/lib` and pip reuses
cached wheels, so building in place can produce a passing test over a broken
artifact — and only on a developer machine, since CI starts clean.

### Coverage of the project brief

| Brief | Covered by |
|---|---|
| A — real installation | `test_packaging.py::test_A_init_on_a_clean_repo` |
| B — state corruption | `test_validation.py` |
| C — gate enforcement | `test_transitions.py::test_C_arbitrary_jump_is_refused`, `test_cli.py::test_C_refuses_to_skip_gates` |
| D — normal progression | `test_cli.py::test_D_and_E_full_journey` |
| E — backward transition | same test, second half |
| G — persistence | `test_cli.py::test_G_agent_edits_to_state_survive_and_validate` |
| F — agent discovery | manual, below |
| H — Spec Kit | `test_handoff.py`; the integration is the handoff and nothing else |

Four tests are `xfail(strict=True)`: they describe known defects as executable
specifications. When one is fixed, the unexpected pass fails the suite, forcing
the marker to be removed rather than quietly forgotten.

## Test F — agent auto-discovery (manual)

Automation cannot cover this one: it tests whether a fresh agent session picks
MVP-OS up on its own.

1. Initialize MVP-OS in a clean repository.
2. Open a new agent session.
3. Do **not** mention MVP-OS.
4. Say: *"I want to start a new project. I have an idea for an application."*

Expected: the agent reads `.mvp-os/methodology.md` and `.mvp-os/state.yml` on
its own, reports that it is at G0, asks for user/problem/observation, and does
not write production code.

## Test H — Spec Kit (not yet applicable)

Deferred until standalone is solid. The Spec Kit bundle was removed in v0.7.0
and has not been reinstated; `detect_spec_kit()` still sets `sdd.provider` but
there is nothing to install.
