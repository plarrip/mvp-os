# MVP-OS v0.7.0 testing

1. Clean repo, non-editable install:
`python -m pip install /path/to/mvp-os-v0.7.0`
then `mvp-os init`. Verify `.mvp-os/methodology.md` exists.

2. Open a fresh agent session without mentioning MVP-OS. Start a project normally.

3. Run `mvp-os validate`. Corrupt schema_version, project type, a hypothesis entry, or sdd.status; validate must return INVALID.

4. From G0 run `mvp-os transition G7`: must be REJECTED. Build valid state and transition through G1/G2/G3. A permitted backward transition such as G3→G2 is allowed.

5. In a separate repo, initialize Spec Kit before `mvp-os init`; verify `sdd.provider: spec-kit`.
