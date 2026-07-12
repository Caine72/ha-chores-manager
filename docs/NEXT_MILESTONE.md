# Next milestone: native options-flow assignment management

## Goal

Complete routine structural administration by adding assignment management to the existing native Home Assistant options flow. This remains occasional administration, so it should reuse the integration repository and Home Assistant's built-in flow UI rather than introduce another frontend repository or installation path.

The options flow remains a user interface only. Integration storage and stable IDs are authoritative, and all mutations must use the existing assignment actions so validation, entity-registry cleanup, lifecycle behavior, and immutable completion history cannot diverge.

## Required options-flow work

1. Add Assignments to the top-level Chores Manager Configure menu.
2. Provide Add assignment and Manage existing assignment paths, with one-level back navigation.
3. Add one assignment at a time through a guided child-then-chore flow.
4. Offer only active children when adding an assignment.
5. After selecting a child, offer only active chores that do not already have an assignment to that child.
6. Explain when no eligible child, chore, or pair is available instead of exposing an invalid form.
7. Show active and inactive assignments when selecting an existing assignment to manage.
8. Label assignment choices using current child and chore display names while preserving stable assignment identity.
9. Show selected child, chore, assignment ID, assignment active state, effective switch availability, and any unavailable parent state above assignment actions.
10. Support activate, deactivate, and confirmed delete operations.
11. Do not provide Edit assignment: changing either relationship endpoint is delete-and-add and creates a new stable assignment identity.
12. Return to the relevant assignment menu after successful mutations.

## Carried-forward UX decisions

- Use precise action labels such as Select child, Select chore, Add assignment, Activate assignment, Deactivate assignment, and Delete assignment.
- Keep navigation one level at a time: assignment actions to Assignments, then Assignments to the main menu.
- Use static translated flow titles and dynamic description placeholders for selected-record context.
- Show destructive consequences before confirmation. Deleting an assignment removes its switch entity and registry entry but preserves completion snapshots until normal retention pruning.
- Keep forms compact and use native selectors; do not add frontend-owned state.

## Backend and architecture requirements

1. Reuse `add_assignment`, `set_assignment_active`, and `delete_assignment` as the mutation path.
2. Preserve assignment stable IDs, monotonic ID counters, labels, entity identity, and independent activation semantics.
3. Distinguish assignment `active` from effective switch availability: an active assignment is unavailable when its child or chore is inactive.
4. Keep the inventory WebSocket contract read-only and backward compatible.
5. Preserve storage version 1 unless implementation discovers a concrete migration requirement.

## Deferred overview analysis

A drill-down options flow is appropriate for individual structural edits but is not an overview interface. A later milestone must evaluate structural and daily overview needs with the current card or cards:

- structural overview of all chores, categories, points, active state, and child assignments;
- daily overview of current completion state by child and chore;
- desktop matrix or table presentation;
- mobile child-grouped or chore-grouped presentation;
- use of the inventory contract plus live assignment entity states;
- optional diagnostics for missing expected entities or inconsistent relationships.

Do not build that overview in this milestone. The options-flow UI cannot provide a strong responsive matrix, and the existing card analysis is the appropriate place to decide its final presentation.

## Constraints

- Do not add batch assignment mutation in this milestone. Single-pair creation avoids partial-success behavior while usage remains infrequent.
- Do not add rewards, allowance logic, notifications, import/export, historical completion editing, or broad analytics.
- Do not expose mutable storage directly.
- Do not make labels or entity names the primary management contract.

## Validation

Run:

```zsh
./scripts/validate --fix
./scripts/validate
git diff --check
git diff
```

Run real HA acceptance when the local HA instance is available:

```zsh
./scripts/run-real-ha-acceptance
```

## Done when

- Assignments are available from the native Chores Manager Configure menu.
- An administrator can add a valid child-to-chore assignment without manually calling an action.
- Existing active and inactive assignments can be inspected, activated, deactivated, and deleted.
- Invalid and duplicate relationship choices are filtered or explained before mutation.
- Deletion confirmation accurately describes entity removal and completion retention.
- Existing actions and the options flow share lifecycle and validation behavior.
- Focused tests and full validation pass without unresolved compatibility risks.
