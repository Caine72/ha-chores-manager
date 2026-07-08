# Chores Manager roadmap

## Product direction

Chores Manager is a private-use Home Assistant custom integration being prepared for a reliable v0.1 release.

Development order:

1. Make the current household workflow reliable.
2. Harden validation, migration, deletion, and diagnostics.
3. Complete real Home Assistant acceptance testing.
4. Prepare and release backend v0.1.
5. Define the backend inventory contract needed by the custom card.
6. Reference the separate custom-card repository after it exists and refactor that card to use this repository's backend contract.
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
- Explicit child, chore, and assignment delete actions with completion-snapshot preservation
- Child and chore metadata editing
- One-time default `Chores` label initialization that preserves user labels
- Focused automated test coverage for implemented behavior
- Release hardening coverage for the registered midnight callback, legacy storage compatibility, and singleton config-flow behavior

## Completed release hardening tests

Automated hardening now covers:

- the actual registered midnight callback through Home Assistant's event/time machinery;
- loading storage created before `label_initialized_assignment_ids` existed;
- singleton config-flow behavior and the stable single-instance abort contract.

## Completed milestone: delete lifecycle

Delete lifecycle is now implemented and validated:

- `delete_assignment`, `delete_chore`, and `delete_child` actions are available.
- Structural records and related live entities are removed intentionally.
- Related entity-registry entries are removed for deleted structure.
- Completion snapshots remain immutable and retained by normal retention pruning.
- Stable ID counters remain monotonic and deleted IDs are not reused.

Validation completed:

- `./scripts/validate --fix`
- `./scripts/validate`
- `git diff --check`
- complete diff review

## Completed milestone: real Home Assistant acceptance

Real Home Assistant acceptance was executed; the detailed acceptance report is a local manual-validation artifact ignored by Git.

Completed acceptance coverage:

- config-entry reload and integration lifecycle checks in a running HA instance;
- create/update/complete/deactivate/reactivate/delete lifecycle behavior;
- identity and stable-ID invariants across metadata edits and reload;
- post-delete entity and registry behavior;
- time-bound midnight/rollover/retention checks via focused automated tests.

No new backend defects were identified in the deterministic acceptance pass.

## Next milestone: backend v0.1 preparation

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

The custom card will not be built in this repository. Add a link to the separate card repository here once that repository is available.

The card still shapes important backend requirements. Before card work starts elsewhere, this repository must define the inventory contract and keep the following principles visible. The separate card will be refactored to consume this repository's interface instead of relying on labels, entity-name matching, or frontend-owned business data.

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

- Hard deletion of completion history
- Editing historical completion snapshots
- Rewards, notifications, or allowance automation inside the integration
- Generic multi-household architecture
- Broad public compatibility or support promises
- Making labels the primary integration/card discovery mechanism
