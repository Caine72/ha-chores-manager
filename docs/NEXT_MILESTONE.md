# Next milestone: native options-flow management for children and chores

## Goal

Make routine Chores Manager administration available from the integration's native Home Assistant options flow. This is the appropriate UI for occasional household setup and maintenance: it adds no second frontend repository, custom resource, or build and installation path.

The options flow is a user interface only. Integration storage and stable IDs remain authoritative. The flow must use the same backend mutation logic as the existing actions so lifecycle and validation behavior cannot diverge.

The existing `chores_manager/inventory` WebSocket command remains the backend contract for future custom-card work. The options flow may share its inventory-building logic internally, but does not require a frontend WebSocket call.

## Required options-flow work

1. Add a Chores Manager options flow reachable from the config entry's Configure action.
2. Provide a top-level menu for Children and Chores management.
3. Show active and inactive records when selecting a child or chore to manage.
4. Support add, edit, activate, deactivate, and delete operations for children.
5. Support add, edit, activate, deactivate, and delete operations for chores.
6. Require an explicit confirmation before deleting a child or chore, including clear notice that related assignments are removed while completion snapshots are retained.
7. Return users to the relevant management menu after a successful mutation so they can perform another maintenance operation without manually calling an action.
8. Use native form validation and translate existing domain errors into useful flow errors.

## Backend and architecture requirements

1. Reuse the existing action/store mutation path rather than duplicating business rules in the options flow.
2. Preserve stable IDs, immutable completion snapshots, entity-registry behavior, and current activation semantics.
3. Keep the config entry's options separate from integration-owned business storage.
4. Do not make labels or entity names the primary management contract.
5. Keep the inventory contract read-only and backward compatible.

## Deferred to the following milestone

- Assignment administration, including add, activate/deactivate, and delete. It requires its own interaction design because the useful UI depends on selecting both a child and a chore and may later benefit from a matrix-style interface.
- Inventory diagnostics for missing entities or inconsistent relationships.
- A separate custom card or richer frontend.

## Constraints

- Do not add rewards, allowance logic, notifications, import/export, historical completion editing, or broad analytics in this milestone.
- Do not expose mutable storage directly.
- Preserve storage version 1 unless a concrete migration requirement is discovered.

## Validation

Run:

```zsh
./scripts/validate --fix
./scripts/validate
git diff --check
git diff
```

Run real HA acceptance when the local HA instance is available and the contract affects live behavior:

```zsh
./scripts/run-real-ha-acceptance
```

## Done when

- The existing config entry exposes a working Configure action for Chores Manager administrators.
- Children and chores can be created and maintained, including inactive records, without manually calling an action.
- Deletion confirmation accurately describes the lifecycle consequences.
- Existing actions and the options flow share lifecycle and validation behavior.
- Validation passes without unresolved contract or compatibility risks.
