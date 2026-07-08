"""Test Chores Manager storage compatibility."""

from copy import deepcopy

from freezegun import freeze_time

from homeassistant.const import ATTR_RESTORED
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

from .common import DOMAIN, NAME

from tests.common import MockConfigEntry

COMPLETION_MODE_INDEPENDENT = "independent"
STORAGE_KEY = f"{DOMAIN}.data"
STORAGE_VERSION = 1

CHORE_SWITCH = "switch.kid_1_chore_1"
WEEKLY_POINTS_SENSOR = "sensor.kid_1_weekly_points"


def _state(hass: HomeAssistant, entity_id: str) -> State:
    """Return an existing Home Assistant state."""
    state = hass.states.get(entity_id)
    assert state is not None
    return state


def _legacy_storage_data() -> dict[str, object]:
    """Create storage data from before label tracking existed."""
    return {
        "next_child_id": 2,
        "next_chore_id": 2,
        "next_assignment_id": 2,
        "next_completion_id": 2,
        "children": {
            "kid_1": {
                "name": "Alex",
                "active": True,
            },
        },
        "chores": {
            "chore_1": {
                "title": "Make the bed",
                "category": "Morning",
                "points": 2,
                "icon": "mdi:bed",
                "active": True,
                "sort_order": 10,
                "completion_mode": COMPLETION_MODE_INDEPENDENT,
            },
        },
        "assignments": {
            "assignment_1": {
                "child_id": "kid_1",
                "chore_id": "chore_1",
                "active": True,
            },
        },
        "completions": {
            "completion_1": {
                "completed_at": "2026-07-08T08:00:00+00:00",
                "local_date": "2026-07-08",
                "child_id": "kid_1",
                "chore_id": "chore_1",
                "assignment_id": "assignment_1",
                "child_name": "Alex",
                "chore_title": "Make the bed",
                "category": "Morning",
                "points": 2,
            },
        },
    }


async def test_storage_without_label_initialized_assignments_loads(
    hass: HomeAssistant,
    hass_storage: dict[str, object],
) -> None:
    """Test legacy storage is upgraded without losing stored structure."""
    await hass.config.async_set_time_zone("UTC")

    legacy_data = _legacy_storage_data()
    expected_children = deepcopy(legacy_data["children"])
    expected_chores = deepcopy(legacy_data["chores"])
    expected_assignments = deepcopy(legacy_data["assignments"])
    expected_completions = deepcopy(legacy_data["completions"])

    assert "label_initialized_assignment_ids" not in legacy_data

    entry = MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={},
    )
    entry.add_to_hass(hass)

    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "data": legacy_data,
    }

    with freeze_time("2026-07-08 12:00:00+00:00"):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        store = entry.runtime_data
        assert store.data["children"] == expected_children
        assert store.data["chores"] == expected_chores
        assert store.data["assignments"] == expected_assignments
        assert store.data["completions"] == expected_completions
        assert store.data["next_child_id"] == 2
        assert store.data["next_chore_id"] == 2
        assert store.data["next_assignment_id"] == 2
        assert store.data["next_completion_id"] == 2
        assert store.data["label_initialized_assignment_ids"] == ["assignment_1"]

        saved_data = hass_storage[STORAGE_KEY]["data"]
        assert saved_data["label_initialized_assignment_ids"] == ["assignment_1"]

    points_state = _state(hass, WEEKLY_POINTS_SENSOR)
    assert points_state.state == "2"
    assert points_state.attributes["child_id"] == "kid_1"
    assert ATTR_RESTORED not in points_state.attributes

    switch_state = _state(hass, CHORE_SWITCH)
    assert switch_state.state == "on"
    assert switch_state.attributes["assignment_id"] == "assignment_1"
    assert ATTR_RESTORED not in switch_state.attributes

    entity_registry = er.async_get(hass)
    points_entry = entity_registry.async_get(WEEKLY_POINTS_SENSOR)
    switch_entry = entity_registry.async_get(CHORE_SWITCH)

    assert points_entry is not None
    assert points_entry.unique_id == "kid_1_weekly_points"
    assert switch_entry is not None
    assert switch_entry.unique_id == "assignment_1"
