# MVP-OS v0.7.0

The LLM owns product reasoning and content. MVP-OS deterministically enforces state structure and gate transitions.

CLI:
`mvp-os init`, `status`, `gate`, `next`, `review`, `validate`, `transition <GATE>`.

`init` installs AGENTS.md, CLAUDE.md, `.mvp-os/state.yml`, `.mvp-os/methodology.md`, and protects `.venv/`.

The methodology is packaged as a Python resource, so normal non-editable installs work.
