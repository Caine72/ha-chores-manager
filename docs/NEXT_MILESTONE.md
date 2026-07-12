# Next milestone: bulk assignment quality improvements

## Goal

Improve native setup efficiency without adding bulk chore-record creation. The milestone covers assigning existing chores in bulk to one child and exposing the backend's existing child selection when creating one new chore.

The options flow remains a user interface over integration-owned storage and backend actions. Stable IDs, validation, entity creation, and completion history remain backend responsibilities.

## Required create-chore improvement

1. Show an active-children multi-select in the Add chore form.
2. Default the selection to all active children, preserving today's behavior when the user makes no change.
3. Allow the user to remove children from the selection before creating the chore.
4. Require at least one active child.
5. Pass the selected stable child IDs through the existing `add_chore` action's `child_ids` field.
6. Keep title, category, points, icon, and sort-order behavior unchanged.
7. Keep creation atomic through the existing store operation: the chore and all selected assignments are created together or not at all.

## Required existing-chore bulk assignment

1. Replace the single-chore add-assignment path with Assign chores to child.
2. Select one active child.
3. Show a multi-select containing active chores that do not already have any assignment to that child.
4. Allow one or more chores to be selected; a one-item selection replaces the existing single-assignment workflow.
5. Show the selected child, chore names, and assignment count in a confirmation step.
6. Create all selected relationships atomically.
7. Return to Assignments after success and refresh eligible choices.
8. Explain when no active child, active chore, or eligible relationship remains.
9. Keep Manage existing assignment unchanged.

## Backend requirements

1. Add an `assign_chores_to_child` action with `child_id` and non-empty `chore_ids`.
2. Add one atomic store method that validates the complete batch before allocating IDs or changing data.
3. Reject the entire batch for an unknown or inactive child, unknown or inactive chore, duplicate chore ID, or existing relationship.
4. On rejection, preserve assignments, counters, registry state, and completion snapshots exactly.
5. On success, allocate monotonic assignment IDs, save once, and let existing listeners create switch entities and labels.
6. Preserve the existing `add_assignment` action for compatibility.
7. Keep storage version 1 and the read-only inventory contract unchanged.

## Carried-forward UX decisions

- Use exact verbs: Select child, Select chores, Assign chores, and Add chore.
- Keep one-level back navigation.
- Use static translated titles and dynamic descriptions.
- Filter invalid choices before submission while retaining authoritative backend validation.
- Do not create frontend-owned business state.

## Explicitly out of scope

- Creating several new chore records in one operation.
- Assigning one existing chore to several children as a separate workflow.
- Editing assignment relationship endpoints.
- Overview, matrix, diagnostics, rewards, notifications, import/export, or historical completion editing.

## Validation

Run:

```zsh
./scripts/validate --fix
./scripts/validate
git diff --check
git diff
```

Manual Home Assistant acceptance must cover the default-all child selection, a reduced child selection, multi-chore assignment, one-item assignment, duplicate filtering, and reload persistence.

## Done when

- A new chore can be assigned to an explicit subset of active children from Configure.
- All active children remain selected by default.
- One or more existing chores can be assigned atomically to one active child.
- Rejected batches cause no partial mutation or stable-ID consumption.
- Existing single-assignment callers remain compatible.
- Focused tests and full validation pass.
