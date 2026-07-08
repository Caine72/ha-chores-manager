# Chores Manager v0.1 roadmap

## Current baseline

- Branch: `main`
- Baseline commit when this roadmap was created: `cb6a82a`
- Validation baseline: 56 passing tests
- Storage version: 1
- Manifest version: 0.0.1

The source code is authoritative if this document becomes stale.

## Completed foundation

- Singleton config entry and integration-owned persistent storage
- Stable child, chore, assignment, and completion IDs
- Weekly-points sensors and daily assignment switches
- Child and chore creation
- Assignment creation between existing children and chores
- Independent completion and undo behavior
- Immutable completion snapshots and weekly point calculation
- Saturday-Friday chore week and two-week completion retention
- Local-midnight refresh behavior
- Child, chore, and assignment activation lifecycles
- Child and chore metadata editing
- One-time default `Chores` label initialization without overwriting user labels
- Focused test coverage alongside implemented features

## Remaining v0.1 sequence

1. **Integration inventory contract**
   - Add a read-only WebSocket command exposing all stored children, chores, and assignments by stable ID.
   - Keep live completion state and controls on Home Assistant entities.
   - This is the next milestone; see `NEXT_MILESTONE.md`.

2. **Release hardening tests**
   - Test the actual registered midnight callback rather than only the store method.
   - Test loading storage created before `label_initialized_assignment_ids` existed.
   - Test config-flow singleton behavior.

3. **Real Home Assistant acceptance**
   - Exercise create, update, deactivate/reactivate, complete/uncomplete, reload, and midnight rollover in a running Home Assistant development instance.
   - Keep the real midnight rollover check as a release gate until callback wiring is covered automatically.

4. **v0.1 documentation and release preparation**
   - Installation and setup
   - Action reference
   - Entity and stable-ID model
   - Retention and week-boundary behavior
   - Upgrade notes and limitations
   - Repository remote/release packaging as appropriate

5. **Integration-aware custom card**
   - Build only after the backend inventory contract and v0.1 reliability work are complete.
   - Use inventory stable IDs for structure and Home Assistant entities for live state/control.
   - Do not use the `Chores` label as the primary discovery contract.

## Outside v0.1

- Hard deletion of children, chores, assignments, or history
- Editing historical completions
- Rewards, notifications, or allowance automation in the integration
- Generic multi-household architecture
- Broad public compatibility/support promises
