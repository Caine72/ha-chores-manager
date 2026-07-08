# Next milestone: integration inventory WebSocket contract

## Goal

Expose the complete stored Chores Manager structure to a future custom card without making labels or currently loaded entities the source of truth.

Implement a read-only Home Assistant WebSocket command:

```text
chores_manager/get_inventory
```

The command must return all stored children, chores, and assignments, including inactive records.

## Architectural boundary

- Storage remains the structural source of truth.
- Stable IDs are the API contract.
- Home Assistant entities remain the live state and control surface.
- Do not return completion history in this milestone.
- Do not add a subscription protocol yet.
- Do not start frontend/card implementation yet.

## Proposed response schema

Use a versioned, deterministic JSON response shaped like:

```json
{
  "schema_version": 1,
  "week": {
    "start": "2026-07-04",
    "end": "2026-07-10"
  },
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
      "icon": "mdi:bed",
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
      "effective_active": true,
      "entity_id": "switch.kid_1_chore_1"
    }
  ]
}
```

`effective_active` is true only when the assignment, its child, and its chore are all active.

Return arrays in deterministic stable-ID order. Prefer numeric stable-ID ordering so IDs such as `kid_2` sort before `kid_10`.

## Backend implementation expectations

- Prefer a dedicated module such as `websocket.py` rather than expanding `services.py`.
- Register the command once during integration setup.
- Resolve the single loaded config entry and its `runtime_data` store at request time.
- Return a WebSocket error when the config entry is not loaded; do not return a misleading empty inventory.
- Keep the handler read-only and synchronous/callback-based unless actual I/O requires otherwise.
- Do not require administrator access for this read-only command; a normal authenticated dashboard user should be able to render the household chore card.
- Derive entity IDs from stable stored IDs using the same convention as the entity platforms.
- Avoid exposing internal counters or label-initialization markers.

Before implementation, inspect current Home Assistant Core WebSocket command patterns and test helpers in `/workspaces/home-assistant-core-dev`.

## Required test coverage

Add focused WebSocket tests covering at least:

1. Empty loaded inventory with schema version and current week bounds.
2. Active children, chores, and assignments with expected stable IDs and entity IDs.
3. Inactive child, chore, and assignment records are still returned.
4. `effective_active` reflects all three lifecycle levels.
5. Completion records are not exposed and completion state does not alter structural inventory.
6. Deterministic stable-ID ordering.
7. A clear WebSocket error when the integration entry is not loaded.
8. Existing 56 tests remain passing.

## Done when

- The command can be called through a Home Assistant WebSocket client.
- The response matches the documented versioned contract.
- No existing action, entity, persistence, label, completion, or lifecycle behavior changes.
- `./scripts/validate --fix` and `./scripts/validate` pass.
- The final diff has been reviewed for API leakage, unstable identity, and accidental history mutation.
