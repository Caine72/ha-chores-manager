# Chores Manager 0.6.0

## Summary

Chores Manager `0.6.0` adds the backend support required by the standalone history card and automatic child portraits.

## Added

- Entity-authorized `chores_manager/current_week_history` reads for one child's current chore week.
- Optional Home Assistant Person association when creating or editing a child.
- `person_entity_id` presentation metadata on child entities and relevant WebSocket responses.
- Native Person selectors in child configuration.

## Authorization

- History requires `read` permission for the child's weekly-points sensor.
- Person association is presentation metadata only and does not affect permissions.
- Inventory and dated correction remain administrator-only.

## Compatibility

- Existing children without a Person association continue to work unchanged.
- The integration stores only the Person entity ID and does not store image files.
- Storage remains version `1`; no migration is required from `0.5.0`.
- Chores Manager Cards `0.3.0` uses these new contracts.

## Final release steps

- [ ] Change `custom_components/chores_manager/manifest.json` from `0.5.0` to `0.6.0`.
- [ ] Run the full repository validation after the version change.
- [ ] Merge the release pull request and confirm checks on `main`.
- [ ] Create and publish tag/release `v0.6.0`.
