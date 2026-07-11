# Chores Manager

[![Validate](https://github.com/Caine72/ha-chores-manager/actions/workflows/validate.yml/badge.svg)](https://github.com/Caine72/ha-chores-manager/actions/workflows/validate.yml)

Chores Manager is a Home Assistant custom integration I use for tracking household chores, daily completions, and weekly points.

> [!IMPORTANT]
> This integration is maintained for my private Home Assistant setup. It is public so it can be installed and updated through HACS as a custom repository. Bug reports are welcome, but there is no support promise, no compatibility guarantee, and no ambition to make this a general-purpose chores platform.
>
> It is also vibe coded with AI assistance. The code is intended to be practical, understandable, and reliable for my household workflow rather than polished as a broadly maintained open-source project.

The backend has a private `0.1.0` baseline and is moving toward `0.2.0` inventory-aware graphical management. It intentionally focuses on integration-owned storage, entities, actions, and the backend inventory contract; the custom card remains a separate milestone.

## What it does

Chores Manager stores children, chores, assignments, and daily completion snapshots in the integration backend. It exposes:

- weekly points sensors per child;
- assignment switches that can be toggled on when a chore is completed today;
- Home Assistant actions for creating, editing, activating, deactivating, and deleting children, chores, and assignments;
- stable IDs so renaming a child or chore does not break entity identity or history.

The chore week runs Saturday through Friday using Home Assistant local time. Completion history is retained for the current chore week and the previous complete chore week.

## Current scope

Current backend development scope is intentionally narrow:

- one Chores Manager config entry;
- backend storage and Home Assistant entities;
- action-based management;
- no custom card in this repository;
- read-only inventory API for graphical management and custom-card work;
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
- Attributes: `child_id`, `kid_name`, `week_start`, `week_end`

Assignment switches:

- Entity ID: `switch.kid_<n>_chore_<n>`
- Unique ID: `assignment_<n>`
- State: `on` when the assignment is completed today, `off` otherwise
- Attributes: `assignment_id`, `child_id`, `kid_name`, `chore_id`, `title`, `category`, `points`, `sort_order`, `completion_mode`

Entity IDs and unique IDs are derived from stable integration IDs, not display names. Renaming a child or chore does not change identity.

## Actions

Actions are available under the `chores_manager` domain.

| Action | Required fields | Optional fields | Behavior |
| --- | --- | --- | --- |
| `add_child` | `name` | none | Creates an active child and weekly-points sensor. |
| `update_child` | `child_id`, `name` | none | Updates the child's display name without changing stable IDs or history. |
| `set_child_active` | `child_id`, `active` | none | Deactivates or reactivates a child. Stored child data, assignments, and history are preserved. |
| `add_chore` | `title`, `category`, `points` | `icon`, `sort_order`, `child_ids` | Creates an active chore and assignments. When `child_ids` is omitted, all active children are assigned. |
| `update_chore` | `chore_id` | `title`, `category`, `points`, `icon`, `sort_order` | Updates editable chore metadata for future state and completions. At least one editable field is required. |
| `set_chore_active` | `chore_id`, `active` | none | Deactivates or reactivates a chore while preserving stored structure and history. |
| `add_assignment` | `child_id`, `chore_id` | none | Assigns an active child to an active chore. Duplicate assignments are rejected. |
| `set_assignment_active` | `assignment_id`, `active` | none | Deactivates or reactivates one assignment while preserving stored structure and history. |
| `delete_assignment` | `assignment_id` | none | Deletes one assignment and its switch registry entry while preserving completion snapshots. |
| `delete_child` | `child_id` | none | Deletes a child, the weekly-points sensor registry entry, and that child's assignment switch registry entries while preserving completion snapshots. |
| `delete_chore` | `chore_id` | none | Deletes a chore and related assignment switch registry entries while preserving completion snapshots. |

Validation trims text input, rejects blank stable IDs, limits names/titles/categories to 100 characters, limits points to 1-100, requires non-negative `sort_order`, and validates icons with Home Assistant's icon selector rules.

## Completion And Retention

Turning an assignment switch on completes that assignment for the current local date. Turning it off removes that assignment's completion for the current local date.

Completion records are immutable snapshots. They store the child name, chore title, category, and points as they existed when the completion was created. Later metadata edits do not rewrite historical completions.

The chore week runs Saturday through Friday using Home Assistant's local time. Weekly points sensors count completions from the current chore week. Storage retention keeps the current chore week and the previous complete chore week; older completions are pruned on load and at local midnight when a new chore week starts.

## Activation And Deletion

Deactivation is reversible. Inactive children, chores, or assignments remain in storage, preserve stable IDs, and keep history. Their live entities become unavailable or are removed from the active switch set until reactivated, depending on the entity type and relationship.

Deletion is intentional structural removal. Deleted children, chores, and assignments are removed from live storage and related entity-registry entries are removed, but immutable completion snapshots remain until normal retention pruning.

Stable ID counters are monotonic. Deleted IDs are not reused.

## Storage Compatibility

The integration uses Home Assistant storage key `chores_manager.data` at storage version `1`. Backend `0.1.0` preserves storage version `1`; no migration is required for this release.

Storage and stable IDs are the source of truth. Labels are initialized for assignment switches as a secondary Home Assistant organization boundary and are not the primary integration contract.

## Inventory API

Chores Manager exposes an admin-only Home Assistant WebSocket command, `chores_manager/inventory`, for read-only structural inventory. The response includes stored children, chores, assignments, active flags, relationships, current entity IDs where available, and current chore-week bounds. It includes inactive records and does not expose completion history. Mutations remain in the existing Home Assistant actions.

See `docs/INVENTORY_CONTRACT.md` for the full response contract.

## Known Limitations

- This is a private-use backend release, not a broad public support commitment.
- Only one config entry is supported.
- There is no graphical management UI or custom card in this repository yet.
- The custom card is not included in this repository.
- Historical completion snapshots cannot be edited or hard-deleted through integration actions.
- Rewards, allowance logic, notifications, import/export, and diagnostics are outside the current backend scope.

## Development Validation

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
