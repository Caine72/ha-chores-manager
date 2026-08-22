# Chores Manager

[![Validate](https://github.com/Caine72/ha-chores-manager/actions/workflows/validate.yml/badge.svg)](https://github.com/Caine72/ha-chores-manager/actions/workflows/validate.yml)

Chores Manager is a Home Assistant custom integration for tracking household chores, daily completions, and weekly points.

The companion [Chores Manager Cards](https://github.com/Caine72/ha-chores-manager-cards) repository provides standalone Lovelace cards.

> [!IMPORTANT]
> This integration is maintained for a private Home Assistant setup and published primarily for HACS installation. Bug reports are welcome, but there is no support or broad compatibility promise.

Development is AI-assisted, with automated validation and live Home Assistant acceptance used to review the resulting behavior.

Released version `0.5.0` provides entity-authorized current/previous weekly-points reads and audited card adjustments. The current development branch adds entity-authorized current-week history and an optional child-to-Person association for compatible card portraits.

## What it does

Chores Manager stores children, chores, assignments, and daily completion snapshots in the integration backend. It exposes:

- weekly points sensors per child;
- assignment switches that can be toggled on when a chore is completed today;
- actions for incrementing or decrementing a child's current-week total;
- Home Assistant actions for creating, editing, activating, deactivating, and deleting children, chores, and assignments;
- an optional Home Assistant Person reference for each child, used only as presentation metadata;
- protected WebSocket contracts for inventory, totals, history, adjustments, and current-week correction;
- stable IDs so renaming a child or chore does not break entity identity or history.

The chore week uses Home Assistant local time and resets after a configurable weekday. Friday is the default, preserving the original Saturday-through-Friday week. Completion history supports the current chore week and the previous complete chore week.

## Current scope

The backend scope is intentionally narrow:

- one Chores Manager config entry;
- backend storage and Home Assistant entities;
- native options-flow management for children, chores, and assignments;
- Home Assistant actions for automation and scripted management;
- no custom card in this repository;
- read-only inventory API for management and custom-card work;
- admin-only current-week correction APIs for a separate correction card;
- entity-authorized current-week history reads for a parent-facing history card;
- entity-authorized weekly totals, current-week history, and point adjustments;
- no rewards, allowance logic, notifications, import/export, or diagnostics.

The integration is named generally because the workflow may grow, but the current implementation is still shaped around one private household setup.

## Installation

### HACS custom repository

1. In Home Assistant, open HACS.
2. Open the HACS custom repositories dialog.
3. Add `https://github.com/Caine72/ha-chores-manager` as an integration repository.
4. Install Chores Manager from HACS.
5. Restart Home Assistant.
6. Add the integration from **Settings > Devices & services > Add integration > Chores Manager**.

### Manual install

1. Copy `custom_components/chores_manager` into the Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from **Settings > Devices & services > Add integration > Chores Manager**.

Only one Chores Manager config entry is supported.

## Entities

Chores Manager creates entities from integration storage.

Weekly points sensors:

- Entity ID: `sensor.kid_<n>_weekly_points`
- Unique ID: `kid_<n>_weekly_points`
- State: points earned by the child in the current chore week
- Unit of measurement: none; the state is a numeric total only
- Attributes: `child_id`, `kid_name`, optional `person_entity_id`, `week_start`, `week_end`

Assignment switches:

- Entity ID: `switch.kid_<n>_chore_<n>`
- Unique ID: `assignment_<n>`
- State: `on` when the assignment is completed today, `off` otherwise
- Attributes: `assignment_id`, `child_id`, `kid_name`, optional `person_entity_id`, `chore_id`, `title`, `category`, `points`, `sort_order`, `completion_mode`

Entity IDs and unique IDs are derived from stable integration IDs, not display names. Renaming a child or chore does not change identity.

## Native management

For occasional household administration, open **Settings -> Devices & services -> Chores Manager -> Configure**. Week settings select the weekday after which a new chore week begins. A changed weekday applies immediately using the selected day's most recent occurrence; for example, changing to reset after Thursday on Saturday starts the current week on the Friday just passed. The same options flow can create, edit, activate, deactivate, and delete children and chores. Each child may optionally reference a Home Assistant Person whose existing profile image is used by compatible cards; Chores Manager does not copy or store that image. It can assign or remove multiple chores for one child, and manage individual active or inactive assignments. It shows active and inactive records and asks for confirmation before removal or deletion; deleting structure removes related live entities while retaining completion history.

## Actions

Actions are available under the `chores_manager` domain.

| Action | Required fields | Optional fields | Behavior |
| --- | --- | --- | --- |
| `add_child` | `name` | `person_entity_id` | Creates an active child and weekly-points sensor with an optional Home Assistant Person association. |
| `update_child` | `child_id`, `name` | `person_entity_id` | Updates the child's display name or Person association without changing stable IDs or history. Omit the Person field to preserve it; pass `null` to clear it. |
| `set_child_active` | `child_id`, `active` | none | Deactivates or reactivates a child. Stored child data, assignments, and history are preserved. |
| `add_chore` | `title`, `category`, `points` | `icon`, `sort_order`, `child_ids` | Creates an active chore and assignments. When `child_ids` is omitted, all active children are assigned. |
| `update_chore` | `chore_id` | `title`, `category`, `points`, `icon`, `sort_order` | Updates editable chore metadata for future state and completions. At least one editable field is required. |
| `set_chore_active` | `chore_id`, `active` | none | Deactivates or reactivates a chore while preserving stored structure and history. |
| `add_assignment` | `child_id`, `chore_id` | none | Assigns an active child to an active chore. Duplicate assignments are rejected. |
| `assign_chores_to_child` | `child_id`, `chore_ids` | none | Atomically assigns one or more active chores to one active child. |
| `remove_chores_from_child` | `child_id`, `chore_ids` | none | Atomically removes one or more assignments and their switch registry entries while preserving completion history. |
| `set_assignment_active` | `assignment_id`, `active` | none | Deactivates or reactivates one assignment while preserving stored structure and history. |
| `delete_assignment` | `assignment_id` | none | Deletes one assignment and its switch registry entry while preserving completion snapshots. |
| `delete_child` | `child_id` | none | Deletes a child, the weekly-points sensor registry entry, and that child's assignment switch registry entries while preserving completion snapshots. |
| `delete_chore` | `chore_id` | none | Deletes a chore and related assignment switch registry entries while preserving completion snapshots. |
| `increment_weekly_counter` | `child_id` | `amount`, `reason` | Adds a positive current-week adjustment. `amount` defaults to `1` and is limited to `1-100`. |
| `decrement_weekly_counter` | `child_id` | `amount`, `reason` | Subtracts from the current-week total without allowing it to become negative. `amount` defaults to `1` and is limited to `1-100`. |

Validation trims text input, rejects blank stable IDs, limits names/titles/categories to 100 characters, limits points to 1-100, requires non-negative `sort_order`, and validates icons with Home Assistant's icon selector rules.

User-originated weekly-counter action calls require Home Assistant `control`
permission for the child's weekly-points sensor. Calls without a user context, such as
trusted internal automations, remain supported.

## Completion and retention

Turning an assignment switch on completes that assignment for the current local date. Turning it off removes that assignment's completion for the current local date.

Completion records are immutable snapshots. They store the child name, chore title, category, and points as they existed when the completion was created. Later metadata edits do not rewrite historical completions.

The chore week resets after the configured weekday using Home Assistant's local time. Friday is the default. Weekly points sensors total current-week completions and manual adjustments. Adjustments record their local date, timestamp, child, point delta, and optional reason; a decrement stores only the amount that can be subtracted from the current total, and is a no-op at zero. Storage retains a rolling 14-day buffer and prunes older completions and adjustments on load and at local midnight. That buffer is sufficient to calculate the current and previous complete chore weeks after any weekday change; data already pruned before upgrading cannot be restored.

## Activation and deletion

Deactivation is reversible. Inactive children, chores, or assignments remain in storage, preserve stable IDs, and keep history. Their live entities become unavailable or are removed from the active switch set until reactivated, depending on the entity type and relationship.

Deletion is intentional structural removal. Deleted children, chores, and assignments are removed from live storage and related entity-registry entries are removed, but immutable completion snapshots remain until normal retention pruning.

Stable ID counters are monotonic. Deleted IDs are not reused.

## Storage compatibility

The integration uses Home Assistant storage key `chores_manager.data` at storage version `1`. Version `0.5.0` preserves storage version `1`; upgrading from `0.1.0`, `0.2.0`, `0.3.0`, or `0.4.0` requires no storage migration. Existing pre-`0.4.0` data gains empty adjustment storage on load.

Storage and stable IDs are the source of truth. An optional Person entity ID is presentation metadata only: it does not link authorization, users, trackers, points, or history. Labels are initialized for assignment switches as a secondary Home Assistant organization boundary and are not the primary integration contract.

## Inventory API

Chores Manager exposes an admin-only Home Assistant WebSocket command, `chores_manager/inventory`, for read-only structural inventory. The response includes stored children, chores, assignments, active flags, relationships, current entity IDs where available, and current chore-week bounds. It includes inactive records and does not expose completion history. Mutations remain in the existing Home Assistant actions.

See `docs/INVENTORY_CONTRACT.md` for the full response contract.

## Weekly points API

The entity-authorized WebSocket commands `chores_manager/weekly_points` and
`chores_manager/adjust_weekly_points` support parent-facing cards without granting
structural administration. The read command returns current and previous complete
chore-week totals and requires `read` permission for the child's weekly-points sensor.
The response also reports whether the caller may adjust that total.
The mutation command creates an audited current-week adjustment and requires `control`
permission for that sensor. Its response includes the applied delta and
backend-confirmed total.

See `docs/WEEKLY_POINTS_CONTRACT.md` for request, response, authorization, and audit
details.

## Current-week history API

The entity-authorized `chores_manager/current_week_history` WebSocket command returns one child's immutable completion snapshots from the backend-calculated current chore week through today. The backend resolves the child's weekly-points sensor and requires Home Assistant `read` permission for that entity. The response includes the child identity, authorized entity ID, backend date window, and completion snapshots, including retained orphan snapshots whose assignment was deleted. Manual point adjustments are intentionally excluded.

See `docs/HISTORY_CONTRACT.md` for the request, response, authorization, and rendering boundaries.

## Admin correction API

For a separate admin card that corrects the current week's history, Chores Manager exposes two admin-only WebSocket commands:

- `chores_manager/current_week_completions` returns completion snapshots from the backend-calculated current chore week through today;
- `chores_manager/set_current_week_completion` idempotently sets one assignment's completion state for a valid date in that window.

The correction API supports inactive existing assignments and removal of history after an assignment is deleted. It rejects future dates, retained previous-week dates, and new completions for deleted assignments. See `docs/CORRECTION_HISTORY_CONTRACT.md` for the full contract.

## Known limitations

- This is a private-use backend release, not a broad public support commitment.
- Only one config entry is supported.
- The custom card is not included in this repository.
- Historical completion correction is limited to the current chore week and requires an admin WebSocket client.
- Rewards, allowance logic, notifications, import/export, and diagnostics are outside the current backend scope.

## Development validation

Before release, run:

```sh
./scripts/validate --fix
./scripts/validate
git diff --check
```

For live Home Assistant acceptance, configure the local untracked `.real_ha_acceptance.env` file and run:

```sh
./scripts/run-real-ha-acceptance
```

Release-specific validation records are kept in `docs/RELEASE_*.md`. Generated live-acceptance artifacts remain local and are not committed.
