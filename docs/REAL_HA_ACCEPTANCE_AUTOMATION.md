# Real HA acceptance automation

Use this when you want the running Home Assistant acceptance workflow to be mostly non-interactive and low-noise.

## Local setup

1. Create a local env file from the example:

```zsh
cp .real_ha_acceptance.env.example .real_ha_acceptance.env
```

2. Set real values in `.real_ha_acceptance.env`:

- `HA_URL`
- `HA_TOKEN`

Optional:

- `HA_CONFIG_DIR` (defaults to `/workspaces/home-assistant-core-dev/config`)
- `HA_ACCEPTANCE_OUTPUT_DIR` (defaults to `/tmp`)

## Run

```zsh
./scripts/run-real-ha-acceptance
```

Optional flags:

```zsh
./scripts/run-real-ha-acceptance --keep-structure
```

## Output

The command prints a compact JSON summary and writes two artifacts:

- `real_ha_acceptance_<stamp>.json`
- `real_ha_acceptance_<stamp>.html`

Artifacts are written to `HA_ACCEPTANCE_OUTPUT_DIR`.

## Notes

- The workflow intentionally mutates live chores_manager structure unless `--keep-structure` is used.
- Midnight/Friday rollover/retention remain covered by automated pytest in `tests/components/chores_manager/test_midnight.py`.
- `docs/REAL_HA_ACCEPTANCE_REPORT.md` is intentionally ignored and can be used as a local manual artifact only.
