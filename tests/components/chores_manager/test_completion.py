"""Test Chores Manager completion and weekly-points behavior."""

from datetime import datetime

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from .common import DOMAIN

from tests.common import MockConfigEntry

CHORE_SWITCH = "switch.kid_1_chore_1"
WEEKLY_POINTS_SENSOR = "sensor.kid_1_weekly_points"


def _state(hass: HomeAssistant, entity_id: str) -> State:
    """Return an existing Home Assistant state."""
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def _call_action(
    hass: HomeAssistant,
    action: str,
    data: dict[str, object],
) -> None:
    """Call a Chores Manager action and wait for entity updates."""
    await hass.services.async_call(
        DOMAIN,
        action,
        data,
        blocking=True,
    )
    await hass.async_block_till_done()


async def _call_switch_action(
    hass: HomeAssistant,
    action: str,
    entity_id: str = CHORE_SWITCH,
) -> None:
    """Call a switch action and wait for Chores Manager updates."""
    await hass.services.async_call(
        "switch",
        action,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()


async def _create_assignment(hass: HomeAssistant) -> None:
    """Create one child and one two-point chore assignment."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
            "icon": "mdi:bed",
        },
    )


async def test_complete_assignment_updates_state_points_and_snapshot(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test completing an assignment and storing an immutable snapshot."""
    await _create_assignment(hass)

    assert _state(hass, CHORE_SWITCH).state == "off"
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "0"

    await _call_switch_action(hass, "turn_on")

    assert _state(hass, CHORE_SWITCH).state == "on"
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"

    store = loaded_config_entry.runtime_data
    assert store.data["next_completion_id"] == 2
    assert list(store.data["completions"]) == ["completion_1"]

    completion = store.data["completions"]["completion_1"]
    assert completion == {
        "completed_at": completion["completed_at"],
        "local_date": dt_util.now().date().isoformat(),
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "assignment_id": "assignment_1",
        "child_name": "Alex",
        "chore_title": "Make the bed",
        "category": "Morning",
        "points": 2,
    }

    completed_at = datetime.fromisoformat(completion["completed_at"])
    assert completed_at.tzinfo is not None


async def test_complete_assignment_is_idempotent(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test repeated completion does not create duplicate records or points."""
    await _create_assignment(hass)

    await _call_switch_action(hass, "turn_on")
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    assert list(store.data["completions"]) == ["completion_1"]
    assert store.data["next_completion_id"] == 2
    assert _state(hass, CHORE_SWITCH).state == "on"
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"


async def test_uncomplete_assignment_removes_today_completion_and_points(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test undoing today's completion and preserving sequential counters."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    await _call_switch_action(hass, "turn_off")

    store = loaded_config_entry.runtime_data
    assert store.data["completions"] == {}
    assert store.data["next_completion_id"] == 2
    assert _state(hass, CHORE_SWITCH).state == "off"
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "0"


async def test_assignments_complete_independently_per_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test each child receives an independent completion and point total."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(hass, "add_child", {"name": "Isabelle"})
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
        },
    )

    await _call_switch_action(hass, "turn_on", "switch.kid_1_chore_1")

    assert _state(hass, "switch.kid_1_chore_1").state == "on"
    assert _state(hass, "switch.kid_2_chore_1").state == "off"
    assert _state(hass, "sensor.kid_1_weekly_points").state == "2"
    assert _state(hass, "sensor.kid_2_weekly_points").state == "0"

    await _call_switch_action(hass, "turn_on", "switch.kid_2_chore_1")

    store = loaded_config_entry.runtime_data
    assert store.data["completions"] == {
        "completion_1": {
            "completed_at": store.data["completions"]["completion_1"]["completed_at"],
            "local_date": dt_util.now().date().isoformat(),
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "assignment_id": "assignment_1",
            "child_name": "Alex",
            "chore_title": "Make the bed",
            "category": "Morning",
            "points": 2,
        },
        "completion_2": {
            "completed_at": store.data["completions"]["completion_2"]["completed_at"],
            "local_date": dt_util.now().date().isoformat(),
            "child_id": "kid_2",
            "chore_id": "chore_1",
            "assignment_id": "assignment_2",
            "child_name": "Isabelle",
            "chore_title": "Make the bed",
            "category": "Morning",
            "points": 2,
        },
    }
    assert _state(hass, "sensor.kid_1_weekly_points").state == "2"
    assert _state(hass, "sensor.kid_2_weekly_points").state == "2"


async def test_completion_persists_across_config_entry_reload(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test completion state and points survive unload and setup."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    assert await hass.config_entries.async_unload(loaded_config_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_config_entry.state is ConfigEntryState.NOT_LOADED

    assert await hass.config_entries.async_setup(loaded_config_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_config_entry.state is ConfigEntryState.LOADED

    assert _state(hass, CHORE_SWITCH).state == "on"
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"
    assert list(loaded_config_entry.runtime_data.data["completions"]) == [
        "completion_1"
    ]


async def test_weekly_points_use_completion_snapshot(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test current chore metadata changes do not rewrite earned points."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = store.data["completions"]["completion_1"]

    assert completion["chore_title"] == "Make the bed"
    assert completion["points"] == 2
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"

    store.data["chores"]["chore_1"]["title"] = "Make the bed properly"
    store.data["chores"]["chore_1"]["points"] = 5
    await store.async_save()
    await hass.async_block_till_done()

    completion = store.data["completions"]["completion_1"]

    assert completion["chore_title"] == "Make the bed"
    assert completion["points"] == 2
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"

    chore_state = _state(hass, CHORE_SWITCH)
    assert chore_state.attributes["title"] == "Make the bed properly"
    assert chore_state.attributes["points"] == 5
