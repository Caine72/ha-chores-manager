# Next milestone: authorized weekly-points card API

## Goal

Add the backend contract discovered during card implementation: an entity-authorized
weekly-points API that exposes the current and previous complete chore-week totals and
supports audited current-week adjustments.

## Authorization

- Reading totals requires Home Assistant `read` permission for the selected child's
  weekly-points sensor.
- Adjusting totals requires Home Assistant `control` permission for that sensor.
- Administrators retain access through their normal unrestricted entity permissions.
- The backend enforces both checks; conditional card rendering is not authorization.

## Contract

1. `chores_manager/weekly_points` accepts `child_id` and returns the sensor entity ID,
   child identity, adjustment capability, and current/previous week bounds and totals.
2. `chores_manager/adjust_weekly_points` accepts `child_id`, a signed non-zero amount
   from `-100` through `100`, and an optional reason.
3. Adjustment responses include the stored adjustment ID (or `null` for a decrement
   no-op at zero), applied delta, and backend-confirmed current total.
4. Existing adjustment actions remain compatible for automations and administration.
5. No card source or frontend-owned business data belongs in this repository.

## Deliverable

Document, implement, test, and live-validate the weekly-points WebSocket contract, then
return to the separate card repository for the frontend milestone.
