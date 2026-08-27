# Chores Manager roadmap

## Current baseline

- [x] Singleton integration-owned storage with stable child, chore, assignment, completion, and adjustment IDs.
- [x] Weekly-points sensors and daily assignment switches.
- [x] Native management for children, chores, assignments, categories, icons, and the reset-after weekday.
- [x] Reversible activation and deliberate structural deletion while retaining immutable history.
- [x] Administrator inventory and current-week correction contracts.
- [x] Entity-authorized weekly totals and authenticated audited adjustments.
- [x] Entity-authorized current-week history.
- [x] Optional child-to-Person presentation metadata without image storage or authorization coupling.
- [x] Automated validation and repeatable real Home Assistant acceptance.

## Current release: 0.7.0

- [x] Remove the caller-specific adjustment capability response.
- [x] Allow authenticated Home Assistant users to adjust weekly points.
- [x] Keep weekly-total reads and administrator commands separately protected.

## Later

- Inventory diagnostics and Home Assistant repair flows for inconsistent relationships.
- Import/export only if it can preserve stable identity and immutable history safely.
- Richer history ranges with explicit retention, authorization, and pagination.
- Optional reward or notification helpers only after the core household workflow remains stable.

## Deliberately outside scope

- Hard deletion or in-place editing of immutable completion snapshots.
- Generic multi-household tenancy.
- Storing child profile images.
- Making Person entities or frontend visibility an authorization boundary.
- Moving rewards, allowance rules, or primary business data into the card repository.

The source code, contract documents, and automated tests are authoritative when roadmap wording becomes stale.
