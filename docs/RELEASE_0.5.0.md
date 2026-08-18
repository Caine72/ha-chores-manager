# Chores Manager 0.5.0

## Summary

Chores Manager `0.5.0` adds the entity-authorized weekly-points contract required by
parent-facing cards. It exposes current and previous complete chore-week totals and
supports audited current-week adjustments without granting structural administration
or correction access.

## Added

- `chores_manager/weekly_points` with current and previous week bounds and totals.
- Backend-derived `can_adjust` capability for the authenticated caller.
- `chores_manager/adjust_weekly_points` with signed amounts, optional reasons, applied
  deltas, adjustment IDs, and backend-confirmed totals.
- `docs/WEEKLY_POINTS_CONTRACT.md`.

## Authorization

- Reading requires Home Assistant `read` permission for the selected child's
  weekly-points sensor.
- Adjusting requires `control` permission for that sensor.
- User-originated legacy adjustment actions apply the same control check.
- Trusted internal calls without a user context remain compatible for automations.

## Compatibility

- Existing entities, stable IDs, services, and correction commands are unchanged.
- Storage remains version `1`; upgrading from `0.4.0` requires no migration.
- Chores Manager Cards `0.2.0` or newer requires this backend version.

## Validation

- `./scripts/validate` (`105 passed`)
- `git diff --check`
- live Home Assistant read and reversible adjustment acceptance
- live desktop and mobile acceptance through the overview card
