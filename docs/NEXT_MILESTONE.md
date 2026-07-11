# Next milestone: v0.2 inventory and graphical management

## Goal

Deliver the v0.2 foundation for inventory-aware graphical management.

The backend must first expose the smallest read-only structure contract needed by the future Chores Manager management UI and custom card. The graphical interface should then use that contract plus existing mutation actions so normal setup and maintenance do not require manually calling Home Assistant actions.

The card or graphical interface may live in a separate repository. This repository owns the backend contract and must keep frontend code from relying on entity-name matching, labels, or frontend-owned business data.

## Required backend work

1. Compare supported Home Assistant transport options for frontend inventory reads.
2. Choose the smallest appropriate interface for read-only structure.
3. Document the selected contract before implementation.
4. Expose stored children, chores, and assignments, including inactive records.
5. Include stable IDs, relationships, current entity IDs where applicable, and current chore-week bounds.
6. Avoid completion-history leakage unless a concrete card requirement is identified.
7. Keep mutation behavior in existing actions.
8. Add focused automated tests for the chosen contract and unload/permission behavior.

## Required graphical management work

1. Use the inventory contract as the source of truth.
2. Use existing Home Assistant actions for mutations instead of storing frontend-owned business data.
3. Support creating, editing, deactivating, reactivating, and deleting children.
4. Support creating, editing, deactivating, reactivating, and deleting chores.
5. Support assigning and unassigning chores to children.
6. Clearly show active and inactive children, chores, and assignments.
7. Refresh inventory after mutations; add live subscriptions only if simple refresh is not enough.
8. Surface basic inventory diagnostics for inconsistent relationships or missing expected entities.

## Constraints

- Do not build the custom card in this repository unless the repository scope is explicitly changed.
- Do not make labels or entity names the primary card contract.
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

- The inventory contract is documented and implemented.
- The contract exposes all active and inactive live structure needed by the future management UI and card.
- Existing actions remain the mutation path.
- The graphical management path can create and maintain children, chores, and assignments without manual action calls.
- Validation passes without unresolved contract or compatibility risks.
- Follow-up analysis of the current card or cards is clearly recorded in `docs/ROADMAP.md`.
