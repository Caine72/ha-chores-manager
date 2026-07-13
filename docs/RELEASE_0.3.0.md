# Chores Manager 0.3.0

## Summary

Chores Manager `0.3.0` finalizes the backend contract needed by the future out-of-repository card. It adds admin-only current-week completion history and correction APIs while keeping the custom card outside this repository.

## Added

- Admin-only `chores_manager/current_week_completions` WebSocket command for current-week completion snapshots.
- Admin-only `chores_manager/set_current_week_completion` WebSocket command for idempotent current-week completion correction.
- Correction support for inactive existing assignments and removal of orphaned current-week history after an assignment is deleted.
- Real Home Assistant acceptance runner coverage for correction history, correction mutation, live switch updates, and weekly-points updates.

## Compatibility

- Storage version remains `1`.
- Upgrading from `0.1.0` or `0.2.0` requires no storage migration.
- Historical correction remains limited to the current Saturday-Friday chore week through today.

## Validation

Release-candidate validation completed on 2026-07-13:

- `./scripts/validate`
- `./scripts/run-real-ha-acceptance`

The generated real Home Assistant acceptance JSON and HTML reports are local artifacts and are not committed.

## Out of scope

- Custom card implementation.
- Historical correction outside the current chore week.
- Rewards, allowance logic, notifications, import/export, and diagnostics.
