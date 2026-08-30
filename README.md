# Chores Manager

Chores Manager is a Home Assistant custom integration for household chores, daily completions, and weekly points.

The companion [Chores Manager Cards](https://github.com/Caine72/ha-chores-manager-cards) repository provides standalone Lovelace cards.

> [!IMPORTANT]
> This integration is maintained for a private Home Assistant setup and published primarily for HACS installation. Bug reports are welcome, but there is no support or broad compatibility promise.

Development is AI-assisted.

## Features

- Manage children, chores, and assignments from Home Assistant.
- Give each chore a category, point value, icon, and display order.
- Complete today's chores through assignment switches.
- Track current and previous chore-week points.
- Choose which weekday ends the chore week.
- Correct current-week completions without rewriting older history.
- Make audited point adjustments that never reduce a total below zero.
- Optionally associate a child with a Home Assistant Person for card portraits.
- Preserve stable identity when children or chores are renamed.

## Installation

### HACS custom repository

1. Open HACS and its custom repositories dialog.
2. Add `https://github.com/Caine72/ha-chores-manager` as an Integration repository.
3. Install Chores Manager and restart Home Assistant.
4. Open **Settings > Devices & services > Add integration > Chores Manager**.

### Manual installation

1. Copy `custom_components/chores_manager` into Home Assistant's `custom_components` directory.
2. Restart Home Assistant.
3. Add Chores Manager from **Settings > Devices & services**.

## Configuration

Open **Settings > Devices & services > Chores Manager > Configure** to manage children, chores, assignments, and the weekday that ends the chore week.

A child may optionally reference a Home Assistant Person. Compatible cards use that Person's existing profile image; Chores Manager stores only the entity ID, not the image.

## Entities

Each child receives a weekly-points sensor:

```text
sensor.kid_<n>_weekly_points
```

Each active child-to-chore assignment receives a switch:

```text
switch.kid_<n>_chore_<n>
```

Entity attributes expose stable child, chore, and assignment IDs together with the presentation data needed by compatible cards. Renaming a child or chore does not change its stable identity.

## Chore weeks and history

The chore week follows Home Assistant local time and ends after the configured weekday. Friday is the default, producing a Saturday-through-Friday week.

Turning an assignment switch on completes that chore for today; turning it off removes today's completion. Completion records retain the child name, chore title, category, and points from the time they were created. Later edits do not rewrite those snapshots.

Shared chores can also be completed manually for the household without assigning
the occurrence or points to a child. Manual occurrences synchronize all related
assignment switches and can be reset independently through Home Assistant actions.

Weekly totals combine completion points with audited manual adjustments. Subtraction is clamped at zero. Current and previous chore-week data are retained in a rolling history window.

Deactivation is reversible. Structural deletion removes the related live entities while retained completion snapshots remain available until normal pruning.

## Actions and APIs

- [Home Assistant actions](docs/ACTIONS.md)
- [WebSocket API index](docs/API.md)
- [Chores Manager Cards](https://github.com/Caine72/ha-chores-manager-cards)

The integration owns storage, week boundaries, permissions, and history. Card visibility is never an authorization boundary.
