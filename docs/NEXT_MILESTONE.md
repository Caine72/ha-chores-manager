# Current milestone: history and Person-association release acceptance

The backend contracts required by the standalone history card and automatic portraits are implemented. The remaining work is coordinated release acceptance with Chores Manager Cards.

## Included

- `chores_manager/current_week_history` scoped to one stable child ID;
- Home Assistant `read` authorization against the child's weekly-points sensor;
- backend-owned current chore-week bounds;
- immutable completion snapshots, including retained orphan history;
- exclusion of manual adjustments from chore history;
- optional `person_entity_id` storage, native child configuration, entity attributes, and API responses;
- no image storage and no authorization relationship through the Person association.

## Acceptance before release

1. Run `./scripts/validate --fix` and `./scripts/validate`.
2. Run the real Home Assistant acceptance workflow without exposing local credentials or artifacts.
3. Verify history with administrator and restricted users.
4. Verify child Person set, preserve, replace, and clear behavior.
5. Validate Overview, Daily, History, and Correction against the matching cards branch.
6. Record version compatibility and release notes before merging.

The card remains in the separate Chores Manager Cards repository. This integration continues to own storage, dates, permissions, and mutation rules.
