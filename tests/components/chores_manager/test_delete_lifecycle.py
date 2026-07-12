"""Test Chores Manager explicit delete lifecycle."""

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .common import DOMAIN

from tests.common import MockConfigEntry

ALEX_SWITCH = "switch.kid_1_chore_1"
ISABELLE_SWITCH = "switch.kid_2_chore_1"
ALEX_POINTS = "sensor.kid_1_weekly_points"
ISABELLE_POINTS = "sensor.kid_2_weekly_points"


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
    entity_id: str = ALEX_SWITCH,
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


async def _create_two_child_assignment(hass: HomeAssistant) -> None:
    """Create two children assigned to one chore."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(hass, "add_child", {"name": "Isabelle"})
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


async def test_delete_assignment_removes_switch_and_allows_new_assignment_id(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment delete removes the switch and preserves history."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])
    entity_registry = er.async_get(hass)
    original_entry = entity_registry.async_get(ALEX_SWITCH)
    assert original_entry is not None
    assert original_entry.unique_id == "assignment_1"
    assert store.data["label_initialized_assignment_ids"] == ["assignment_1"]

    await _call_action(
        hass,
        "delete_assignment",
        {"assignment_id": "assignment_1"},
    )

    assert store.data["children"] == {"kid_1": {"name": "Alex", "active": True}}
    assert store.data["chores"]["chore_1"]["title"] == "Make the bed"
    assert store.data["assignments"] == {}
    assert store.data["completions"] == {"completion_1": completion}
    assert store.data["label_initialized_assignment_ids"] == []
    assert store.data["next_assignment_id"] == 2
    assert hass.states.get(ALEX_SWITCH) is None
    assert entity_registry.async_get(ALEX_SWITCH) is None
    assert _state(hass, ALEX_POINTS).state == "2"

    await _call_action(
        hass,
        "add_assignment",
        {"child_id": "kid_1", "chore_id": "chore_1"},
    )

    assert store.data["assignments"] == {
        "assignment_2": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert store.data["next_assignment_id"] == 3
    new_entry = entity_registry.async_get(ALEX_SWITCH)
    assert new_entry is not None
    assert new_entry.unique_id == "assignment_2"
    assert _state(hass, ALEX_SWITCH).state == "off"
    assert store.data["completions"] == {"completion_1": completion}


async def test_remove_chores_from_child_rejects_batch_atomically(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test one missing relationship prevents every requested removal."""
    await _create_assignment(hass)
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Feed the cat",
            "category": "Evening",
            "points": 3,
        },
    )
    await _call_action(
        hass,
        "delete_assignment",
        {"assignment_id": "assignment_2"},
    )

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "remove_chores_from_child",
            {
                "child_id": "kid_1",
                "chore_ids": ["chore_1", "chore_2"],
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "missing_assignments"
    assert exc_info.value.translation_placeholders == {"chore_ids": "chore_2"}
    store = loaded_config_entry.runtime_data
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert store.data["next_assignment_id"] == 3
    assert hass.states.get(ALEX_SWITCH) is not None


async def test_delete_child_removes_sensor_assignments_and_switches(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test child delete removes live child structure but preserves snapshots."""
    await _create_two_child_assignment(hass)
    await _call_switch_action(hass, "turn_on", ALEX_SWITCH)

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])
    entity_registry = er.async_get(hass)
    assert store.data["label_initialized_assignment_ids"] == [
        "assignment_1",
        "assignment_2",
    ]

    await _call_action(hass, "delete_child", {"child_id": "kid_1"})

    assert store.data["children"] == {"kid_2": {"name": "Isabelle", "active": True}}
    assert store.data["assignments"] == {
        "assignment_2": {
            "child_id": "kid_2",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert store.data["completions"] == {"completion_1": completion}
    assert store.data["label_initialized_assignment_ids"] == ["assignment_2"]
    assert store.data["next_child_id"] == 3
    assert store.data["next_assignment_id"] == 3
    assert store.get_current_week_points("kid_1") == 2
    assert hass.states.get(ALEX_POINTS) is None
    assert hass.states.get(ALEX_SWITCH) is None
    assert entity_registry.async_get(ALEX_POINTS) is None
    assert entity_registry.async_get(ALEX_SWITCH) is None
    assert _state(hass, ISABELLE_POINTS).state == "0"
    assert _state(hass, ISABELLE_SWITCH).state == "off"

    await _call_action(hass, "add_child", {"name": "Alex"})

    assert "kid_3" in store.data["children"]
    assert store.data["next_child_id"] == 4
    new_sensor = _state(hass, "sensor.kid_3_weekly_points")
    assert new_sensor.state == "0"
    assert new_sensor.attributes["child_id"] == "kid_3"


async def test_delete_chore_removes_assignments_and_switches(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test chore delete removes live chore structure but preserves snapshots."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])
    entity_registry = er.async_get(hass)

    await _call_action(hass, "delete_chore", {"chore_id": "chore_1"})

    assert store.data["children"] == {"kid_1": {"name": "Alex", "active": True}}
    assert store.data["chores"] == {}
    assert store.data["assignments"] == {}
    assert store.data["completions"] == {"completion_1": completion}
    assert store.data["label_initialized_assignment_ids"] == []
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 2
    assert hass.states.get(ALEX_SWITCH) is None
    assert entity_registry.async_get(ALEX_SWITCH) is None
    assert _state(hass, ALEX_POINTS).state == "2"

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

    assert store.data["chores"]["chore_2"]["title"] == "Make the bed"
    assert store.data["assignments"] == {
        "assignment_2": {
            "child_id": "kid_1",
            "chore_id": "chore_2",
            "active": True,
        }
    }
    new_entry = entity_registry.async_get("switch.kid_1_chore_2")
    assert new_entry is not None
    assert new_entry.unique_id == "assignment_2"


@pytest.mark.parametrize(
    ("action", "data", "translation_key", "translation_placeholders"),
    [
        pytest.param(
            "delete_assignment",
            {"assignment_id": "assignment_999"},
            "unknown_assignment",
            {"assignment_id": "assignment_999"},
            id="assignment",
        ),
        pytest.param(
            "delete_child",
            {"child_id": "kid_999"},
            "unknown_child",
            {"child_id": "kid_999"},
            id="child",
        ),
        pytest.param(
            "delete_chore",
            {"chore_id": "chore_999"},
            "unknown_chore",
            {"chore_id": "chore_999"},
            id="chore",
        ),
    ],
)
async def test_delete_rejects_unknown_targets(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
    action: str,
    data: dict[str, object],
    translation_key: str,
    translation_placeholders: dict[str, str],
) -> None:
    """Test delete actions reject unknown stable IDs."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            action,
            data,
            blocking=True,
        )

    assert exc_info.value.translation_key == translation_key
    assert exc_info.value.translation_placeholders == translation_placeholders
    assert loaded_config_entry.runtime_data.data["children"] == {}
    assert loaded_config_entry.runtime_data.data["chores"] == {}
    assert loaded_config_entry.runtime_data.data["assignments"] == {}


async def test_delete_is_unknown_after_first_delete(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test repeated delete follows unknown-ID behavior after removal."""
    await _create_assignment(hass)

    await _call_action(
        hass,
        "delete_assignment",
        {"assignment_id": "assignment_1"},
    )

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "delete_assignment",
            {"assignment_id": "assignment_1"},
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_assignment"
    assert exc_info.value.translation_placeholders == {"assignment_id": "assignment_1"}
    assert loaded_config_entry.runtime_data.data["assignments"] == {}


async def test_reload_after_delete_does_not_restore_removed_entities(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test deleted entities stay removed across config entry reload."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")
    await _call_action(hass, "delete_child", {"child_id": "kid_1"})

    entity_registry = er.async_get(hass)
    assert hass.states.get(ALEX_POINTS) is None
    assert hass.states.get(ALEX_SWITCH) is None
    assert entity_registry.async_get(ALEX_POINTS) is None
    assert entity_registry.async_get(ALEX_SWITCH) is None

    assert await hass.config_entries.async_unload(loaded_config_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_config_entry.state is ConfigEntryState.NOT_LOADED

    assert await hass.config_entries.async_setup(loaded_config_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_config_entry.state is ConfigEntryState.LOADED

    assert hass.states.get(ALEX_POINTS) is None
    assert hass.states.get(ALEX_SWITCH) is None
    assert entity_registry.async_get(ALEX_POINTS) is None
    assert entity_registry.async_get(ALEX_SWITCH) is None
    assert loaded_config_entry.runtime_data.data["completions"]["completion_1"] == {
        "completed_at": loaded_config_entry.runtime_data.data["completions"][
            "completion_1"
        ]["completed_at"],
        "local_date": loaded_config_entry.runtime_data.data["completions"][
            "completion_1"
        ]["local_date"],
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "assignment_id": "assignment_1",
        "child_name": "Alex",
        "chore_title": "Make the bed",
        "category": "Morning",
        "points": 2,
    }
