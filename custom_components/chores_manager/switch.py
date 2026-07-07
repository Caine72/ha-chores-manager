"""Switch entities for Chores Manager."""

from typing import Any

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .labels import async_initialize_assignment_label
from .models import ChoresManagerConfigEntry
from .storage import ChoresManagerStore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChoresManagerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Chores Manager assignment switches."""
    store = entry.runtime_data
    known_assignment_ids: set[str] = set()

    def async_add_new_assignments() -> None:
        """Add switches for newly discovered active assignments."""
        new_assignment_ids = [
            assignment_id
            for assignment_id, assignment in store.data["assignments"].items()
            if assignment["active"]
            and store.data["children"][assignment["child_id"]]["active"]
            and store.data["chores"][assignment["chore_id"]]["active"]
            and assignment_id not in known_assignment_ids
        ]

        if not new_assignment_ids:
            return

        known_assignment_ids.update(new_assignment_ids)

        async_add_entities(
            [
                ChoreAssignmentSwitch(store, assignment_id)
                for assignment_id in new_assignment_ids
            ]
        )

    async_add_new_assignments()

    entry.async_on_unload(store.async_add_listener(async_add_new_assignments))


class ChoreAssignmentSwitch(SwitchEntity):
    """Represent one child-to-chore assignment."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        store: ChoresManagerStore,
        assignment_id: str,
    ) -> None:
        """Initialize the assignment switch."""
        self._store = store
        self._assignment_id = assignment_id

        assignment = store.data["assignments"][assignment_id]

        self.entity_id = (
            f"{SWITCH_DOMAIN}.{assignment['child_id']}_{assignment['chore_id']}"
        )
        self._attr_unique_id = assignment_id

    @property
    def name(self) -> str:
        """Return the entity name."""
        assignment = self._assignment
        child = self._store.data["children"][assignment["child_id"]]
        chore = self._store.data["chores"][assignment["chore_id"]]

        return f"{child['name']} {chore['title']}"

    @property
    def icon(self) -> str:
        """Return the chore icon."""
        return self._chore["icon"]

    @property
    def available(self) -> bool:
        """Return whether the assignment is available."""
        return (
            self._assignment["active"]
            and self._child["active"]
            and self._chore["active"]
        )

    @property
    def is_on(self) -> bool:
        """Return whether the chore is completed today."""
        return self._store.is_assignment_completed_today(self._assignment_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return chore assignment attributes."""
        assignment = self._assignment
        child = self._child
        chore = self._chore

        return {
            "assignment_id": self._assignment_id,
            "child_id": assignment["child_id"],
            "kid_name": child["name"],
            "chore_id": assignment["chore_id"],
            "title": chore["title"],
            "category": chore["category"],
            "points": chore["points"],
            "sort_order": chore["sort_order"],
            "completion_mode": chore["completion_mode"],
        }

    async def async_added_to_hass(self) -> None:
        """Initialize registry metadata and subscribe to data changes."""
        await super().async_added_to_hass()

        await async_initialize_assignment_label(
            self.hass,
            self._store,
            self._assignment_id,
            self.registry_entry,
        )

        self.async_on_remove(
            self._store.async_add_listener(
                self.async_write_ha_state,
            )
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mark the chore completed today."""
        await self._store.async_complete_assignment(self._assignment_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Remove today's chore completion."""
        await self._store.async_uncomplete_assignment(self._assignment_id)

    @property
    def _assignment(self):
        """Return assignment data."""
        return self._store.data["assignments"][self._assignment_id]

    @property
    def _child(self):
        """Return child data."""
        return self._store.data["children"][self._assignment["child_id"]]

    @property
    def _chore(self):
        """Return chore data."""
        return self._store.data["chores"][self._assignment["chore_id"]]
