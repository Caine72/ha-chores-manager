# Chores Manager 0.9.0

## Summary

Chores Manager `0.9.0` adds zero-point manual completion for shared chores so a
household job can be recorded without attributing it to a child.

## Added

- `chores_manager.complete_chore_manually` for today's shared occurrence.
- `chores_manager.reset_manual_chore_completion` for reversing that occurrence.
- `completed_manually` on synchronized assignment switches while active.
- Immutable zero-point completion snapshots with no child claimant.

## Behavior

- Manual completion requires an active shared chore with an active assignment.
- Every related assignment switch becomes `on` without awarding child points.
- Repeating completion or reset is idempotent.
- Resetting a manual occurrence does not remove a child-claimed occurrence.

## Compatibility

- Existing child claims and independent chores keep their current behavior.
- Storage remains version `1`; no migration is required from `0.8.0`.
