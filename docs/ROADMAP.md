# Chores Manager roadmap

## Product direction

Chores Manager is a private-use Home Assistant custom integration with a reliable v0.1 backend baseline and a v0.2 inventory and graphical management release.

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

## Completed milestone: native options-flow management for children and chores

The Chores Manager config entry now exposes a native Configure flow for occasional administration without another frontend repository or installation path.

Completed behavior includes:

- top-level Children and Chores management menus;
- create, edit, activate/deactivate, and confirmed delete operations;
- active and inactive record selection using current display metadata and stable IDs;
- existing-or-new chore category selection;
- a collapsed native advanced section for icon and sort order;
- selected-record context above action menus;
- precise submit verbs and one-level back navigation;
- reuse of existing Home Assistant actions as the mutation path;
- focused options-flow lifecycle and validation tests.

## Completed milestone: native options-flow assignment management

The native Configure flow now supports guided single assignment creation and management of active and inactive assignments. It filters existing relationships, distinguishes assignment state from effective parent availability, and reuses existing actions for activation and confirmed deletion.

## Completed milestone: bulk assignment quality improvements

Before v0.2 release preparation, improve setup efficiency without adding bulk creation of chore records.

The Add chore form should expose the existing `child_ids` capability as an active-children multi-select. All active children are selected by default, preserving current behavior, while the user may choose a smaller subset before creating the chore.

For existing chores, replace single assignment creation with Assign chores to child: select one active child, select one or more eligible active chores, confirm the batch, and create every relationship atomically. Add the symmetric Remove chores from child flow for deleting one or more existing relationships while preserving completion history. Backend validation must reject either full batch before mutation if any requested relationship is invalid.

Do not add a separate one-chore-to-many-existing-children workflow or bulk chore-record creation in this milestone.

The milestone passed automated and manual acceptance. Version v0.2 release completion covers stale documentation cleanup, live acceptance coverage, version bump, release notes, tag, and GitHub release.

## Future overview requirement

Drill-down flows are effective for changing one record but do not provide a good picture of the household's current state. After assignment administration, evaluate overview requirements alongside the existing card or cards rather than forcing a table into the options-flow UI.

The analysis must distinguish:

- structural overview: all chores, categories, points, active states, child relationships, and missing expected entities;
- daily overview: current completion state for every child-to-chore relationship.

A likely desktop presentation is a chore-by-child matrix or compact table. Mobile should use child-grouped or chore-grouped lists rather than compressing the matrix. The inventory WebSocket contract supplies structural data, while assignment entity states supply live completion state. Do not build this overview as part of assignment management.

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
