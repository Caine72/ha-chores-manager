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

# Run only the non-admin correction and native Activity attribution scenario.
./scripts/run-real-ha-acceptance --scenario correction-actor --quiet
```

## Output

The command prints a compact JSON summary and writes two artifacts:

- `real_ha_acceptance_<stamp>.json`
- `real_ha_acceptance_<stamp>.html`

Artifacts are written to `HA_ACCEPTANCE_OUTPUT_DIR`.

## Notes

- The full workflow intentionally mutates live chores_manager structure unless `--keep-structure` is used. The `correction-actor` scenario creates and removes only its own child and chore.
- The runner uses the Home Assistant development environment's `aiohttp` installation to create a temporary non-admin user, exercise the authenticated WebSocket correction contract, and remove the credentials and user afterward.
- It verifies current-week correction history, add/remove correction behavior, live switch state, weekly-points updates, and user context on corrected weekly-points state.
- Local-midnight refresh, configured weekday rollover, and retention remain covered by automated pytest in `tests/components/chores_manager/test_midnight.py`.
- `docs/REAL_HA_ACCEPTANCE_REPORT.md` is intentionally ignored and can be used as a local manual artifact only.
