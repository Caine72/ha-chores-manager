# Next milestone: backend inventory contract

## Goal

Define and implement the smallest read-only backend contract needed by the future Chores Manager custom card.

The card will live in a separate repository. This milestone only prepares the backend interface it needs so the card does not rely on entity-name matching, labels, or frontend-owned business data.

## Required work

1. Compare supported Home Assistant transport options for frontend inventory reads.
2. Choose the smallest appropriate interface for read-only structure.
3. Document the selected contract before implementation.
4. Expose stored children, chores, and assignments, including inactive records.
5. Include stable IDs, relationships, current entity IDs where applicable, and current chore-week bounds.
6. Avoid completion-history leakage unless a concrete card requirement is identified.
7. Keep mutation behavior in existing actions.
8. Add focused automated tests for the chosen contract and unload/permission behavior.

## Constraints

- Do not build the custom card in this repository.
- Do not make labels or entity names the primary card contract.
- Do not add broad administrative features in this milestone.
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
- The contract exposes all active and inactive live structure needed by the future card.
- Existing actions remain the mutation path.
- Validation passes without unresolved contract or compatibility risks.
- Follow-up custom-card work is clearly recorded in `docs/ROADMAP.md`.
