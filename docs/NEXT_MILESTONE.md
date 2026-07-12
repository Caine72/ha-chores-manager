# Current milestone: current-week correction history

## Goal

Provide the first backend contract required by an out-of-repository admin card that corrects the current week's completion history. The milestone is read-only: it establishes stable completion history and current-week boundaries before any correction mutation is introduced.

## Inputs

1. The current card source and configuration, treated as read-only reference.
2. The v0.2 inventory WebSocket contract.
3. Stored completion snapshots and the current Saturday-Friday week.

## Required analysis

1. Define an admin-only current-week completion history WebSocket command.
2. Return stable IDs, snapshot metadata, and local dates.
3. Expose the backend-owned correction window from the current week start through today.
4. Include history whose referenced assignment was later deleted.
5. Document how the history response combines with structural inventory.
6. Add focused response, access-control, retention-boundary, and orphan-history tests.

## Constraints

- Integration storage and stable IDs remain the source of truth.
- The current week is the only mutable correction window; the retained previous week remains read-only.
- No card implementation, resource, helper entity, To-do list, counter, or script is included in this repository.
- This milestone adds no correction mutation.

## Deliverable

An implemented and documented read-only correction history contract, ready for the next mutation milestone.
