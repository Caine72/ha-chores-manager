# Current milestone: 0.6.0 release

The backend contracts required by the standalone history card and automatic portraits are implemented and documented.

## Included

- `chores_manager/current_week_history` scoped to one stable child ID;
- Home Assistant `read` authorization against the child's weekly-points sensor;
- backend-owned current chore-week bounds;
- immutable completion snapshots, including retained orphan history;
- exclusion of manual adjustments from chore history;
- optional `person_entity_id` storage, native child configuration, entity attributes, and API responses;
- no image storage and no authorization relationship through the Person association.

## Remaining

1. Change the manifest version to `0.6.0`.
2. Run final validation after the version change.
3. Merge and confirm checks on `main`.
4. Publish `v0.6.0` before releasing Chores Manager Cards `0.3.0`.

See [the prepared release notes](RELEASE_0.6.0.md).
