# Next milestone: real Home Assistant acceptance

## Goal

Exercise Chores Manager in a running Home Assistant development instance before backend v0.1 preparation.

This milestone should validate the real config-entry flow, service actions, entity registry behavior, labels, persisted storage, reload behavior, and date-bound refreshes as Home Assistant users will experience them.

## Scope

This is primarily an acceptance and defect-finding milestone. Production changes are allowed only when acceptance testing exposes a concrete defect, and each defect fix should include a focused automated regression test.

Do not add a new backend API surface during this milestone.

## Required acceptance workflow

Run the integration in a Home Assistant development instance and verify:

1. Install or reload the integration through the config-entry flow.
2. Add children.
3. Add chores and assignments.
4. Rename children and chores.
5. Complete and undo assignments.
6. Deactivate and reactivate children, chores, and assignments.
7. Reload Home Assistant and confirm identity, state, labels, and history remain correct.
8. Validate ordinary midnight rollover.
9. Validate Friday-to-Saturday week rollover.
10. Confirm current and previous week retention behavior.

## What to inspect

During the workflow, explicitly check:

- stable entity IDs and unique IDs stay derived from `kid_*`, `chore_*`, and `assignment_*` IDs;
- mutable child names and chore titles update display metadata without changing identity;
- completion snapshots preserve the earned points and stored names/titles from completion time;
- the `Chores` label remains present on assignment switch entities without overwriting user-added labels;
- inactive children, chores, and assignments preserve stored objects, registry identity, labels, and history;
- reload restores weekly-points sensors and assignment switches without `restored` placeholder state;
- Saturday-Friday week bounds and two-week completion retention match the automated tests.

## Constraints

- Preserve storage version 1 unless a real migration need is discovered.
- Preserve stable IDs and registry identity.
- Preserve completion snapshots.
- Preserve label behavior.
- Do not add an inventory API in this milestone.
- Do not add a WebSocket command in this milestone.
- Do not start custom-card development in this repository.
- Keep the future out-of-repo custom card and its backend prerequisites in mind when evaluating acceptance results.
- Keep any defect fixes incremental and covered by focused tests.

## Validation

After any code or test change, run:

```zsh
./scripts/validate --fix
./scripts/validate
git diff --check
git diff
```

For acceptance-only documentation or notes, at minimum review `git diff --check` and the complete diff.

## Done when

- The full acceptance workflow has been exercised in a running Home Assistant development instance.
- Any discovered defect is either fixed with an automated regression test or documented as an explicit follow-up risk.
- Existing automated validation remains passing after any fix.
- No unrelated behavior or architecture is changed.
- The acceptance result and any follow-up risks are recorded before backend v0.1 preparation begins.
