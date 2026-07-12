# Next milestone: card and overview analysis

## Goal

Analyze the current Home Assistant card or cards and define the next user-facing interaction milestone. The integration backend is now ready for an out-of-repository admin correction card, but the card itself is not part of this repository.

## Inputs

1. `docs/INVENTORY_CONTRACT.md` for stable structural inventory.
2. `docs/CORRECTION_HISTORY_CONTRACT.md` for current-week admin correction.
3. `docs/ADMIN_CORRECTION_MANUAL_TEST.md` for the integration release-candidate test.
4. The existing card source and configuration, treated only as reference.
5. Desktop and mobile daily workflows.

## Required analysis

1. Replace entity-name matching, labels, helper entities, counters, To-do lists, and automation scripts with integration-owned stable IDs and WebSocket contracts.
2. Separate daily completion interaction, structural overview, and admin correction views.
3. Define a desktop chore-by-child overview and a mobile grouped alternative.
4. Define card loading, error, empty, inactive, orphan-history, and access-denied states.
5. Decide whether the current card should be refactored, replaced, or split.
6. Define repository ownership, installation, and release boundaries.

## Constraints

- The card stores no long-term business data.
- Structural data comes from inventory; current-week correction history comes from the correction contract; live current-day interaction uses assignment switches.
- The current Saturday-Friday week through today is the only correctable interval.
- No card source, resource, helper entity, To-do list, counter, or automation script belongs in this repository.

## Deliverable

Document a concrete card milestone with view structure, data flow, repository decision, acceptance criteria, migration plan, and deferred functionality.
