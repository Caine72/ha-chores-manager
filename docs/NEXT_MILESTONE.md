# Next milestone: authorized current-week history API

## Goal

Add the backend contract required by the standalone history card: an entity-authorized
read API for one child's current configured chore week.

## Authorization

- Reading history requires Home Assistant `read` permission for the selected child's
  weekly-points sensor.
- Administrators retain access through their normal unrestricted entity permissions.
- The backend enforces the check; conditional card rendering is not authorization.

## Contract

1. `chores_manager/current_week_history` accepts a stable `child_id`.
2. The response includes the child identity, authorized sensor entity ID, backend week
   bounds, and only that child's completion snapshots.
3. Deleted-assignment snapshots remain readable while retained.
4. Manual adjustments are excluded because this is chore history, not an audit ledger.
5. The existing admin-only correction commands remain separate and unchanged.
6. No card source or frontend-owned business data belongs in this repository.

## Deliverable

Document, implement, test, and live-validate the history WebSocket contract, then
return to the separate card repository for the frontend milestone.
