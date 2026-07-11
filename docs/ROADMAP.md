# Chores Manager roadmap

## Product direction

Chores Manager is a private-use Home Assistant custom integration moving from the reliable backend v0.1 baseline toward a v0.2 inventory and graphical management release.

Development order:

1. Make the current household workflow reliable.
2. Harden validation, migration, deletion, and diagnostics.
3. Complete real Home Assistant acceptance testing.
4. Prepare and release backend v0.1.
5. Define the backend inventory contract needed by graphical management and the custom card.
6. Add a graphical management interface for children, chores, and assignments so routine changes do not require manually calling actions.
7. After v0.2, analyze the current custom card or cards and refactor them to use this repository's backend contract.
8. Only then consider broader administration, generalization, or distribution.

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
- time-bound midnight/rollover/retention checks via focused automated tests;
- repeatable live acceptance automation via `./scripts/run-real-ha-acceptance` with local untracked env config.

No new backend defects were identified in the deterministic acceptance pass.

## Completed milestone: backend v0.1 preparation

Backend v0.1 preparation is complete:

- root README documents installation, setup, actions, entities, stable-ID guarantees, week boundaries, retention, activation, deletion, storage compatibility, and limitations;
- integration version is `0.1.0`;
- HACS custom-repository metadata and a minimal repository icon are present;
- intended repository URL is `https://github.com/Caine72/ha-chores-manager`;
- storage version remains `1` with no migration required;
- backend v0.1 still does not require a custom card or custom WebSocket command.

## Completed milestone: v0.2 inventory contract

The read-only, admin-only `chores_manager/inventory` WebSocket command is implemented and documented in `docs/INVENTORY_CONTRACT.md`.

It exposes all stored children, chores, and assignments, including inactive records, stable relationships, entity-registry IDs where available, and current chore-week bounds. It intentionally excludes completion history and has no subscription; consumers refresh after mutations.

## Next milestone: native options-flow management for children and chores

v0.2 should make the integration manageable without manually calling Home Assistant actions for normal setup and maintenance. The first graphical-management step is a native options flow, not a separate frontend repository: these changes are occasional administration and Home Assistant already provides the needed forms, selectors, permissions, mobile support, and installation path.

This milestone introduces a Configure action for the Chores Manager config entry with a top-level Children and Chores menu. It supports create, edit, activate/deactivate, and confirmed delete operations, including active and inactive records.

The options flow is only an interface. Storage, stable IDs, lifecycle behavior, and validation remain backend-owned. It must reuse existing action/store mutation logic rather than creating a frontend-owned data model or a second set of business rules.

Assignment administration is deliberately deferred to the following milestone. Its child-and-chore selection workflow needs a dedicated interaction design; the default all-child assignment behavior means it is expected to be used less often than chore maintenance.

## Integration-aware custom card

The custom card will not be built in this repository. Add a link to the separate card repository here once that repository is available.

The card still shapes important backend requirements. Before card work starts elsewhere, this repository must define the inventory contract and keep the following principles visible. After v0.2 is complete, analyze the current card or cards used for interacting with the integration, then refactor the separate card to consume this repository's interface instead of relying on labels, entity-name matching, or frontend-owned business data.

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

- advanced validation and inventory diagnostics;
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
