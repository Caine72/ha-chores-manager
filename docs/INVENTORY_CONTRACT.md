# Chores Manager inventory contract

The inventory contract is the backend-owned read-only structure API for future graphical management and custom-card work.

## Transport

Use the Home Assistant WebSocket API command `chores_manager/inventory`.

Request:

```json
{
  "type": "chores_manager/inventory"
}
```

The command is admin-only. If Chores Manager does not have exactly one loaded config entry, the command returns a WebSocket `not_found` error.

## Response

```json
{
  "children": [
    {
      "child_id": "kid_1",
      "name": "Alex",
      "active": true,
      "points_entity_id": "sensor.kid_1_weekly_points"
    }
  ],
  "chores": [
    {
      "chore_id": "chore_1",
      "title": "Make the bed",
      "category": "Morning",
      "points": 2,
      "icon": "mdi:checkbox-marked-circle-outline",
      "active": true,
      "sort_order": 10,
      "completion_mode": "independent"
    }
  ],
  "assignments": [
    {
      "assignment_id": "assignment_1",
      "child_id": "kid_1",
      "chore_id": "chore_1",
      "active": true,
      "switch_expected": true,
      "switch_entity_id": "switch.kid_1_chore_1"
    }
  ],
  "week": {
    "start": "2026-07-11",
    "end": "2026-07-17"
  }
}
```

## Contract rules

- Integration storage and stable IDs are the structural source of truth.
- Children, chores, and assignments include active and inactive records.
- Entity IDs come from the Home Assistant entity registry so user-renamed entities are respected.
- `points_entity_id` or `switch_entity_id` is `null` when no registry entry exists.
- `switch_expected` is `true` only when the assignment, child, and chore are all active.
- Completion history is not exposed by this contract.
- Mutations remain in existing Home Assistant actions.
- Consumers should refresh inventory after mutations; this contract does not provide a subscription.
