# Chores Manager roadmap

## Product direction

Chores Manager is a private-use Home Assistant custom integration being prepared for a reliable v0.1 release.

Development order:

1. Make the current household workflow reliable.
2. Harden validation, migration, and diagnostics.
3. Complete real Home Assistant acceptance testing.
4. Prepare and release backend v0.1.
5. Define the backend inventory contract needed by the custom card.
6. Build the integration-aware custom card.
7. Only then consider broader administration, generalization, or distribution.

The source code and automated tests are authoritative if this document becomes stale.

## Current baseline

- Singleton config entry with integration-owned persistent storage
- Stable IDs for children, chores, assignments, and completions
- Weekly-points sensors and daily assignment switches
- Child, chore, and assignment creation
- Independent completion and undo behavior
- Immutable completion snapshots
- Saturday-Friday chore week
- Current and previous complete week retained
- Local-midnight state refresh
- Child, chore, and assignment activation lifecycles
- Child and chore metadata editing
- One-time default `Chores` label initialization that preserves user labels
- Focused automated test coverage for implemented behavior

## Next milestone: release hardening tests

Strengthen confidence in the existing backend before adding another API surface.

Required work:

1. Test the actual registered midnight callback through Home Assistant's event/time machinery, not only the store method.
2. Test loading storage created before `label_initialized_assignment_ids` existed.
3. Test singleton config-flow behavior:
   - first setup succeeds;
   - a second config entry cannot be created;
   - abort reason is correct and translated.
4. Add any small regression tests discovered while implementing the above.
5. Keep behavior and storage format unchanged unless a concrete defect requires a minimal correction.

Done when:

- The new tests exercise integration wiring rather than duplicating existing unit coverage.
- Existing lifecycle, entity, completion, retention, and label behavior remains unchanged.
- `./scripts/validate --fix` passes.
- `./scripts/validate` passes.
- The complete diff has been reviewed.

## Following milestone: real Home Assistant acceptance

Exercise the integration in a running Home Assistant development instance.

Acceptance workflow:

1. Install or reload the integration through the config-entry flow.
2. Add children.
3. Add chores and assignments.
4. Rename children and chores.
5. Complete and undo assignments.
6. Deactivate and reactivate children, chores, and assignments.
7. Reload Home Assistant and confirm identity, state, labels, and history remain correct.
8. Validate ordinary midnight rollover.
9. Validate Friday-to-Saturday week rollover.
10. Confirm current and previous week retention behavior.

Record defects as focused follow-up changes with automated regression tests.

## Backend v0.1 preparation

After automated hardening and real acceptance:

- Write installation and setup documentation.
- Document actions and their validation behavior.
- Document entities, attributes, and stable-ID guarantees.
- Document week boundaries and completion retention.
- Document activation versus deletion semantics.
- Document known limitations.
- Review storage compatibility and upgrade behavior.
- Set the release version and prepare repository packaging.

The backend v0.1 release does not require a custom card or a custom WebSocket command.

## Custom-card prerequisite: inventory contract

Before building the custom card, define a read-only contract that exposes integration-owned structure not reliably available from active entity states alone.

The contract will likely need:

- all stored children, including inactive children;
- all stored chores, including inactive chores;
- all stored assignments, including inactive assignments;
- stable IDs and relationships;
- current entity IDs where applicable;
- current chore-week bounds;
- no mutation of stored data;
- no completion-history leakage unless explicitly required by a later feature.

At this milestone, compare supported Home Assistant transport options and choose the smallest appropriate interface. A custom WebSocket command is one possible option, not a predetermined requirement.

The decision should consider:

- whether the card can operate entirely from `hass.states` and normal action calls;
- whether a service action with response data is suitable;
- whether a custom WebSocket command is justified for frontend-only structural queries;
- whether subscriptions are needed, or simple refresh after mutations is sufficient;
- permissions and unload behavior;
- entity-registry renames and inactive records.

Document the chosen contract before implementation.

## Integration-aware custom card

Build only after the backend v0.1 work and inventory-contract decision are complete.

Card principles:

- Integration storage and stable IDs are the structural source of truth.
- Home Assistant entities provide live state and control.
- The `Chores` label remains a secondary external scope boundary, not the card's primary contract.
- The frontend must not become the long-term business-data store.
- Build the DOM once and update only changed data.
- Ignore unrelated Home Assistant state changes.
- Preserve clear mobile hierarchy and large tap targets.

## Later administration and helper functionality

After the current workflow and card are reliable, consider:

- administrative child/chore/assignment management;
- validation and inventory diagnostics;
- repair flows for inconsistent stored relationships;
- import/export or backup helpers;
- richer historical views;
- optional reward or notification helpers.

Each feature must preserve stable identity and completion history.

## Outside backend v0.1

- Hard deletion of children, chores, assignments, or history
- Editing historical completion snapshots
- Rewards, notifications, or allowance automation inside the integration
- Generic multi-household architecture
- Broad public compatibility or support promises
- Making labels the primary integration/card discovery mechanism
