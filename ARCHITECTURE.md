# MVP-OS architecture

```text
                    MVP-OS CORE
          Lean / Product / Evidence / Gates
                       │
             ┌─────────┴─────────┐
             │                   │
       Standalone mode     Optional SDD adapter
             │                   │
        MVP-OS runtime       Spec Kit (planned)
             │                   │
             └─────────┬─────────┘
                       ↓
                  Implementation
```

The core MUST NOT require `.specify/`, OpenSpec, Superpowers or any other SDD
framework. Standalone is the primary mode, not a degraded one.

## Three levels, never duplicated

```text
AGENTS.md                  how the agent should behave
.mvp-os/methodology.md     what MVP-OS is and what its principles are
.mvp-os/state.yml          what is happening in this specific project
```

`AGENTS.md` must not restate the methodology. It points at it.

## Modules

| Module | Responsibility |
|---|---|
| `state.py` | State file layout, defaults, load/save, Spec Kit detection |
| `lifecycle.py` | Gate names, the transition graph, per-gate requirements |
| `validation.py` | `validate_shape` (types) and `validate_state` (full check) |
| `cli.py` | Command surface, resource installation, agent instructions |
| `resources/` | Files installed into a project: methodology, gitignore template |

`validate_shape` is split out so the read commands can distinguish a state that
cannot be parsed from one that is merely incomplete. A cleared `next_action` is
a normal working state; a `project` that is a string is not.

## Single source of truth

Product state lives in `.mvp-os/state.yml`, never in `.specify/mvp-os/`. There
are no parallel states.

## Spec Kit integration

Not implemented in this repository. `detect_spec_kit()` sets `sdd.provider`, but
the extension, commands and workflows that existed in v0.6.0 were removed in
v0.7.0 and nothing installs them. When reinstated, the integration must use
native Spec Kit primitives and stay optional: the bundle is distribution and
composition, not the MVP-OS runtime.
