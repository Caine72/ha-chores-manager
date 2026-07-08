"""Sensor entities for Chores Manager."""

import asyncio
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import UNIT_POINTS
from .models import ChoresManagerConfigEntry
from .storage import ChoresManagerStore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChoresManagerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Chores Manager sensors."""
    store = entry.runtime_data
    child_entities: dict[str, ChildWeeklyPointsSensor] = {}
    reconcile_lock = asyncio.Lock()

    async def async_reconcile_children() -> None:
        """Add and remove child sensors to match storage data."""
        async with reconcile_lock:
            desired_child_ids = set(store.data["children"])

            removed_child_ids = child_entities.keys() - desired_child_ids
            for child_id in tuple(removed_child_ids):
                entity = child_entities.pop(child_id)
                await entity.async_remove()

            new_child_ids = desired_child_ids - child_entities.keys()
            if not new_child_ids:
                return

            new_entities = {
                child_id: ChildWeeklyPointsSensor(store, child_id)
                for child_id in sorted(new_child_ids)
            }
            child_entities.update(new_entities)
            async_add_entities(new_entities.values())

    @callback
    def async_schedule_reconciliation() -> None:
        """Schedule child entity reconciliation."""
        entry.async_create_task(
            hass,
            async_reconcile_children(),
            "Reconcile Chores Manager child sensors",
        )

    await async_reconcile_children()

    entry.async_on_unload(store.async_add_listener(async_schedule_reconciliation))


class ChildWeeklyPointsSensor(SensorEntity):
    """Represent a child's points for the current chore week."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:star-circle"
    _attr_native_unit_of_measurement = UNIT_POINTS
    _attr_should_poll = False

    def __init__(
        self,
        store: ChoresManagerStore,
        child_id: str,
    ) -> None:
        """Initialize the weekly points sensor."""
        self._store = store
        self._child_id = child_id

        self.entity_id = f"sensor.{child_id}_weekly_points"
        self._attr_unique_id = f"{child_id}_weekly_points"

    @property
    def name(self) -> str:
        """Return the sensor name."""
        return f"{self._child['name']} weekly points"

    @property
    def native_value(self) -> int:
        """Return the points earned during the current chore week."""
        return self._store.get_current_week_points(self._child_id)

    @property
    def available(self) -> bool:
        """Return whether the child is active."""
        return self._child["active"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return information about the points period."""
        week_start, week_end = self._store.get_current_week_bounds()

        return {
            "child_id": self._child_id,
            "kid_name": self._child["name"],
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to Chores Manager data changes."""
        await super().async_added_to_hass()

        @callback
        def async_write_state_if_present() -> None:
            """Write state when the child still exists."""
            if self._child_id in self._store.data["children"]:
                self.async_write_ha_state()

        self.async_on_remove(
            self._store.async_add_listener(
                async_write_state_if_present,
            )
        )

    @property
    def _child(self):
        """Return the stored child data."""
        return self._store.data["children"][self._child_id]
