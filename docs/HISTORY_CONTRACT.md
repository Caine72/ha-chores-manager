# Chores Manager current-week history contract

The history contract supports a standalone parent-facing card that lists one child's
completed chores in the current configured chore week. It replaces legacy To-do,
template-sensor, and Markdown pipelines; those helpers are not runtime dependencies.

## Read transport

Request the entity-authorized Home Assistant WebSocket command:

```json
{"type": "chores_manager/current_week_history", "child_id": "kid_1"}
```

The backend resolves the child's weekly-points sensor and requires Home Assistant
`read` permission for that entity. Administrator status, card visibility, and child
names are not authorization boundaries.

## Response

```json
{
  "child_id": "kid_1",
  "child_name": "Alex",
  "points_entity_id": "sensor.kid_1_weekly_points",
  "window": {"start": "2026-08-21", "end": "2026-08-22"},
  "completions": [
    {
      "completion_id": "completion_1",
      "assignment_id": "assignment_1",
      "assignment_exists": true,
      "child_id": "kid_1",
      "chore_id": "chore_1",
      "local_date": "2026-08-22",
      "completed_at": "2026-08-22T08:00:00+00:00",
      "child_name": "Alex",
      "chore_title": "Feed the cat",
      "category": "Cat",
      "points": 1
    }
  ]
}
```

The window starts at the backend-configured current week boundary and ends today in
Home Assistant local time. Completions are scoped to the requested stable child ID and
sorted by local date then stable completion ID. Immutable snapshots remain readable
when their assignment was later deleted. Manual point adjustments are excluded because
this contract describes completed chores rather than the total's audit ledger.

Consumers must render the returned dates and snapshots and must not calculate a fixed
reset weekday or parse display text as business data.
