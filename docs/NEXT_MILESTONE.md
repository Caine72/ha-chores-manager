# Next milestone: card and overview analysis

## Goal

After v0.2.0, analyze the current Home Assistant card or cards used with Chores Manager and define the next user-facing interaction milestone. Do not start implementation until the existing cards, daily workflow, and overview requirements have been examined together.

## Inputs

1. The current card source and configuration.
2. The v0.2 inventory WebSocket contract.
3. Assignment switch states and weekly-points sensors.
4. Real desktop and mobile interaction patterns.
5. The distinction between occasional administration and daily chore completion.

## Required analysis

1. Identify card-owned business data, entity-name matching, label assumptions, and duplicated backend rules.
2. Map existing card behavior to stable child, chore, and assignment IDs.
3. Separate structural inventory from live completion state.
4. Evaluate a compact chore-by-child matrix for desktop.
5. Evaluate child-grouped or chore-grouped lists for mobile.
6. Define loading, unavailable, empty, inactive, and partial-entity states.
7. Decide whether the current card should be refactored, replaced, or split into overview and daily-interaction views.
8. Define the repository boundary and installation impact before adding another frontend repository.

## Constraints

- Integration storage and stable IDs remain the structural source of truth.
- Home Assistant entities remain the live state and control surface.
- The `Chores` label is a secondary organization boundary, not the primary data contract.
- The card must not become a second business-data store.
- Options flow remains the administration surface; the card focuses on overview and daily interaction.
- No card implementation belongs in the v0.2.0 release.

## Deliverable

Document a concrete card milestone with view structure, data flow, repository decision, migration implications, acceptance criteria, and explicitly deferred functionality.
