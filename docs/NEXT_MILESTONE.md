# Next milestone: separate card repository kickoff

## Goal

Start card implementation in a separate repository using the backend contracts finalized for Chores Manager `0.4.0`. The backend repository is functionally complete for the currently documented scope unless card work identifies a specific missing backend contract or defect.

## Inputs

1. `docs/INVENTORY_CONTRACT.md` for stable structural inventory.
2. `docs/CORRECTION_HISTORY_CONTRACT.md` for current-week admin correction.
3. `docs/ADMIN_CORRECTION_MANUAL_TEST.md` for release-candidate contract checks.
4. The `increment_weekly_counter` and `decrement_weekly_counter` actions for current-week manual adjustments.
5. Existing card analysis and household workflow notes outside this repository.
6. Desktop and mobile daily workflows.

## Constraints

- No card source, resource, helper entity, To-do list, counter, or automation script belongs in this repository.
- The card stores no long-term business data.
- Structural data comes from inventory; current-week correction history comes from the correction contract; live current-day interaction uses assignment switches; weekly adjustments use the integration actions.
- The current Saturday-Friday week through today is the only correctable interval.
- Backend changes discovered during card work should be documented as new backend milestones before implementation.

## Deliverable

Create the separate card repository and implement the user-facing daily, overview, and admin correction views against the documented integration contracts.
