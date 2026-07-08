# Next milestone: release hardening tests

## Goal

Strengthen confidence in the existing Chores Manager backend before adding another API surface or starting custom-card work.

This milestone should primarily add tests. Production changes are allowed only when a new test exposes a concrete defect.

## Required coverage

### Registered midnight callback

Test the callback registered by `async_track_time_change` through Home Assistant's event/time test helpers.

Cover:

- ordinary midnight refreshes daily assignment state;
- weekly points remain in the same Saturday-Friday week;
- Friday-to-Saturday rollover starts a new week;
- retained completion pruning still follows the two-week policy.

Do not merely call `store.async_handle_local_midnight()` directly; that behavior already has coverage.

### Legacy storage compatibility

Load stored data that predates `label_initialized_assignment_ids`.

Verify:

- setup succeeds;
- the missing key is initialized;
- existing children, chores, assignments, and completions are preserved;
- upgraded data is saved;
- entities restore correctly.

### Singleton config flow

Test the config flow as a singleton integration.

Verify:

- the first user flow creates the config entry;
- a later user flow aborts when an entry already exists;
- the abort reason is stable and translated;
- no duplicate household entry is created.

## Constraints

- Preserve storage version 1 unless a real migration need is discovered.
- Preserve stable IDs and registry identity.
- Preserve completion snapshots.
- Preserve label behavior.
- Do not add an inventory API in this milestone.
- Do not add a WebSocket command in this milestone.
- Do not start custom-card development.
- Keep changes incremental and focused.

## Validation

Run:

```zsh
./scripts/validate --fix
./scripts/validate
git diff --check
git diff
```

## Done when

- The integration wiring described above is covered.
- Existing tests remain passing.
- Any discovered defect has a focused regression test.
- No unrelated behavior or architecture is changed.
