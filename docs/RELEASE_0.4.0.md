# Chores Manager 0.4.0

## Summary

Chores Manager `0.4.0` adds frontend-callable current-week counter adjustments for cards and automations. It keeps completion history immutable while recording manual changes as auditable adjustment records.

## Added

- `chores_manager.increment_weekly_counter` to add a current-week adjustment for a child.
- `chores_manager.decrement_weekly_counter` to subtract from a current-week total without allowing it to become negative.
- Optional `reason` values on adjustments, alongside local date, timestamp, child, and point delta.
- Adjustment retention and pruning matching the existing current-and-previous-chore-week completion policy.

## Changed

- Weekly total sensors no longer report a native unit of measurement. Their state remains numeric and cards own labels such as `points`.

## Compatibility

- Existing entity IDs and names, including `sensor.kid_<n>_weekly_points`, are unchanged.
- Storage version remains `1`.
- Upgrading from `0.1.0`, `0.2.0`, or `0.3.0` requires no storage migration. Empty adjustment storage is added on load.

## Validation

Release-candidate validation completed on 2026-07-13:

- `./scripts/validate --fix`
- `./scripts/validate` (`98 passed`)
- `git diff --check`
- `./scripts/run-real-ha-acceptance` (PASS)
- GitHub Actions: HACS, Hassfest, and Project validation

The generated real Home Assistant acceptance JSON and HTML reports are local artifacts and are not committed.

## Out of scope

- Custom card implementation.
- Historical adjustments outside the current chore week.
- Rewards, allowance logic, notifications, import/export, and diagnostics.
