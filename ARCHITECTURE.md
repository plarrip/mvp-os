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

`detect_spec_kit()` records the provider; `mvp-os handoff` emits the product
context. That is the entire integration, and it is deliberately one-directional:
MVP-OS installs nothing into Spec Kit and imports nothing from it.

The alternative was rebuilding the v0.6.0 bundle, which shipped a Spec Kit
extension with five `speckit.mvp.*` commands. Two findings against it, both from
testing against Spec Kit 1.0.11 rather than reading its docs:

- A bundle cannot carry its own extension. `_locate_bundled_extension()` looks
  only in Spec Kit's core pack or source checkout, so installing a bundle
  offline fails even when the built `.zip` embeds the extension. Components must
  come from a catalog. The v0.6.0 manifest passes `specify bundle validate` and
  still cannot be installed.
- The commands used the wrong namespace. Spec Kit requires the extension's own
  (`mvp-os.hypothesis`, surfaced as `speckit.mvp-os.hypothesis`); v0.6.0 used
  `speckit.mvp.hypothesis` and is rejected at install time.

Both are fixable. The reason not to fix them is that those five commands restate
guidance the methodology already gives the agent, in a second place, coupled to
one provider's extension format.
