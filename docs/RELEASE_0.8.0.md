# Chores Manager 0.8.0

## Summary

Chores Manager `0.8.0` adds shared chores for household jobs that should be
completed once per day by any one of their assigned children.

## Added

- `shared` completion mode alongside the existing `independent` mode.
- Atomic first-child claiming across every assignment for the shared chore.
- Synchronized `on` and `off` state across those assignment switches.
- `completed_at`, `completed_by_child_id`, `completed_by_child_name`, and
  `completion_assignment_id` switch attributes while an occurrence is complete.
- Shared-occurrence behavior in current-week correction and real Home Assistant
  acceptance coverage.

## Behavior

- The first child to turn on an assigned switch owns the immutable completion
  snapshot and receives the chore's points.
- A second child cannot create a duplicate completion for the same shared chore
  and local date.
- Turning off any assignment switch removes that shared daily occurrence.
- Separate shared chores remain independent, so one child can claim both a
  morning and an evening occurrence on the same day.

## Compatibility

- Existing chores remain `independent` and keep their current behavior.
- New chores default to `independent` unless `shared` is selected.
- Administrators can select the mode when creating or editing a chore.
- Storage remains version `1`; no migration is required from `0.7.0`.
