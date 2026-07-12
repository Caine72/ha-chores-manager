# Chores Manager correction history contract

The correction history contract supports an out-of-repository admin card that corrects the current week's completion history. It does not source, depend on, or package any card implementation.

## Current-week boundary

The backend calculates the correction window using Home Assistant local time:

- start: the current Saturday-Friday chore week's Saturday;
- end: today;
- excluded: future dates and every date in the retained previous week.

The backend, rather than the card, owns this validation.

## Read transport

Use the admin-only Home Assistant WebSocket command:

```json
{
  "type": "chores_manager/current_week_completions"
}
```

The response contains the correction window and completion snapshots whose local date is within that window.

```json
{
  "window": {
    "start": "2026-07-11",
    "end": "2026-07-12"
  },
  "completions": [
    {
      "completion_id": "completion_1",
      "assignment_id": "assignment_1",
      "assignment_exists": true,
      "child_id": "kid_1",
      "chore_id": "chore_1",
      "local_date": "2026-07-12",
      "completed_at": "2026-07-12T12:00:00+00:00",
      "child_name": "Alex",
      "chore_title": "Make the bed",
      "category": "Morning",
      "points": 2
    }
  ]
}
```

Completion records are sorted by local date, then stable completion ID. The response includes historical snapshots even when the referenced assignment was later deleted. The assignment_exists field distinguishes those orphan records from live assignment history.

Call chores_manager/inventory separately for current children, chores, assignments, entity IDs, and presentation metadata. Consumers refresh both read commands after a correction; neither command subscribes to updates.

## Planned mutation contract

The next milestone will add an admin-only, idempotent mutation for current-week correction:

- set an existing assignment's completed state for one valid local date;
- add at most one completion per assignment and local date;
- remove an existing completion by stable completion ID, including orphan completion history;
- permit correction of inactive but still-existing assignments;
- reject new completions for deleted assignments, future dates, and dates before the current week start;
- retain completion snapshots without rewriting their historical metadata.
