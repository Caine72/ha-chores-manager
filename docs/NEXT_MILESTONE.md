# Current milestone: current-week completion correction

## Goal

Add the backend-owned, admin-only mutation required by the correction card. It must make an assignment completed or incomplete for a selected current-week date without relying on a card helper, a To-do list, counters, or an automation script.

## Inputs

1. The current card source and configuration, treated as read-only reference.
2. The v0.2 inventory WebSocket contract.
3. The merged current-week completion history contract.

## Required analysis

1. Define one idempotent admin-only WebSocket correction command.
2. Add a snapshot for an existing assignment and a valid current-week date.
3. Remove a matching completion by assignment ID and local date, including orphan history.
4. Allow inactive but existing assignments to receive a correction.
5. Reject future dates, previous-week dates, invalid dates, and new completions for deleted assignments.
6. Refresh entity listeners so today's switch and weekly points reflect corrections immediately.
7. Add focused mutation, access-control, idempotence, orphan-history, and date-boundary tests.

## Constraints

- Integration storage and stable IDs remain the source of truth.
- The current week is the only mutable correction window; the retained previous week remains read-only.
- No card implementation, resource, helper entity, To-do list, counter, or script is included in this repository.
- The card remains separate and receives no source files from this repository.

## Deliverable

An implemented and documented current-week correction mutation, ready for final integration acceptance preparation.
