# Weekly points WebSocket contract

The weekly-points API lets cards read retained totals and make audited current-week
adjustments without granting structural administration or correction access.

## Read totals

Request:

```json
{"type": "chores_manager/weekly_points", "child_id": "kid_1"}
```

The caller must have Home Assistant `read` permission for the child's weekly-points
sensor. The response contains:

```json
{
  "child_id": "kid_1",
  "child_name": "Avery",
  "person_entity_id": "person.avery",
  "points_entity_id": "sensor.kid_1_weekly_points",
  "can_adjust": true,
  "current_week": {"start": "2026-08-15", "end": "2026-08-21", "points": 5},
  "previous_week": {"start": "2026-08-08", "end": "2026-08-14", "points": 12}
}
```

The previous interval is the complete configured chore week immediately before the
current week. The backend calculates both intervals from the configured reset-after
weekday; consumers must use the returned dates rather than calculating weekdays.
Totals include completion snapshots and audited adjustments.
`can_adjust` reports whether this caller has `control` permission for the resolved
weekly-points sensor, allowing cards to omit the adjustment workflow without inferring
authorization from administrator status or frontend visibility rules.

`person_entity_id` is omitted when no Person is associated with the child. It is an optional portrait hint only and does not affect entity permissions.

## Adjust the current total

Request:

```json
{
  "type": "chores_manager/adjust_weekly_points",
  "child_id": "kid_1",
  "amount": -2,
  "reason": "Duplicate reward"
}
```

The caller must have Home Assistant `control` permission for the child's weekly-points
sensor. `amount` is a signed non-zero integer from `-100` through `100`; `reason` is
optional, trimmed, and limited to 200 characters. Positive amounts increment and
negative amounts decrement. Decrements clamp at zero.

Zero is an invariant for every weekly total, not only manual adjustments. Removing a
completion through a chore switch or the dated correction API also floors the total at
zero. If an existing audited decrement would otherwise make that removal negative, the
backend stores an audited balancing adjustment. Legacy negative raw data is likewise
reported as zero.

The response contains `adjustment_id`, the requested and applied amounts, and the
backend-confirmed current total. `adjustment_id` is `null` and `applied_amount` is zero
when decrementing a zero total.

Every applied change is stored as an adjustment with timestamp, local date, child,
point delta, and optional reason. Completion history is not rewritten.

## Authorization boundary

Authorization is enforced by the backend against the resolved weekly-points entity.
Hiding a card or control does not grant or remove access. Inventory and correction
commands keep their separate administrator-only policies.
