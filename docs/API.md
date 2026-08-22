# WebSocket API

Chores Manager exposes focused Home Assistant WebSocket contracts for companion cards and management clients.

| Contract | Purpose | Authorization |
| --- | --- | --- |
| [Inventory](INVENTORY_CONTRACT.md) | Children, chores, assignments, entity IDs, and week bounds | Administrator |
| [Weekly points](WEEKLY_POINTS_CONTRACT.md) | Current/previous totals and audited adjustments | Weekly-points sensor `read` or `control` |
| [Current-week history](HISTORY_CONTRACT.md) | One child's immutable completion snapshots | Weekly-points sensor `read` |
| [Current-week correction](CORRECTION_HISTORY_CONTRACT.md) | Read and set dated current-week completions | Administrator |

The backend calculates week boundaries and enforces authorization. Consumers use stable IDs and returned dates rather than display names, entity-name matching, or a fixed reset weekday.
