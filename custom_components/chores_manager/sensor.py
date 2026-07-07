"""Sensor entities for Chores Manager."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
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
    known_child_ids: set[str] = set()

    def async_add_new_children() -> None:
        """Add sensors for newly discovered active children."""
        new_child_ids = [
            child_id
            for child_id, child in store.data["children"].items()
            if child["active"] and child_id not in known_child_ids
        ]

        if not new_child_ids:
            return

        known_child_ids.update(new_child_ids)

        async_add_entities(
            [ChildWeeklyPointsSensor(store, child_id) for child_id in new_child_ids]
        )

    async_add_new_children()

    entry.async_on_unload(store.async_add_listener(async_add_new_children))


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

        self.async_on_remove(
            self._store.async_add_listener(
                self.async_write_ha_state,
            )
        )

    @property
    def _child(self):
        """Return the stored child data."""
        return self._store.data["children"][self._child_id]
