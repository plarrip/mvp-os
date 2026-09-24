# MVP-OS architecture v0.4

```text
                    MVP-OS CORE
          Lean / Product / Evidence / Gates
                       │
             ┌─────────┴─────────┐
             │                   │
       Standalone mode     Optional SDD adapter
             │                   │
        MVP-OS runtime       Spec Kit bundle
             │                   │
             └─────────┬─────────┘
                       ↓
                  Implementation
```

The core MUST NOT require `.specify/`, OpenSpec, Superpowers or any other SDD framework.

Spec Kit integration uses native Spec Kit primitives: extension, workflows and bundle.
The bundle is distribution/composition, not the MVP-OS runtime.
