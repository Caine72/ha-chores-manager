"""Test Chores Manager child metadata updates."""

from unittest.mock import patch

import pytest

from homeassistant.const import ATTR_ENTITY_ID, ATTR_RESTORED, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .common import DOMAIN

from tests.common import MockConfigEntry

ALEX_POINTS = "sensor.kid_1_weekly_points"
ISABELLE_POINTS = "sensor.kid_2_weekly_points"
ALEX_CHORE_1 = "switch.kid_1_chore_1"
ALEX_CHORE_2 = "switch.kid_1_chore_2"
ISABELLE_CHORE_1 = "switch.kid_2_chore_1"
ISABELLE_CHORE_2 = "switch.kid_2_chore_2"


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
    entity_id: str = ALEX_CHORE_1,
) -> None:
    """Call a switch action and wait for Chores Manager updates."""
    await hass.services.async_call(
        "switch",
        action,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()


async def _create_child_assignment(hass: HomeAssistant) -> None:
    """Create one child and one chore assignment."""
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


async def _create_two_children_and_two_chores(hass: HomeAssistant) -> None:
    """Create two children assigned to two chores."""
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
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Feed the cat",
            "category": "Evening",
            "points": 3,
            "icon": "mdi:cat",
        },
    )


async def test_update_child_refreshes_selected_child_live_metadata(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test renaming one child refreshes all of that child's live entities."""
    await _create_two_children_and_two_chores(hass)

    await _call_action(
        hass,
        "update_child",
        {
            "child_id": "kid_1",
            "name": "  Alexander  ",
        },
    )

    store = loaded_config_entry.runtime_data
    assert store.data["children"]["kid_1"]["name"] == "Alexander"
    assert store.data["children"]["kid_2"]["name"] == "Isabelle"

    alex_points = _state(hass, ALEX_POINTS)
    assert alex_points.name == "Alexander weekly points"
    assert alex_points.attributes["kid_name"] == "Alexander"

    for entity_id, title in (
        (ALEX_CHORE_1, "Make the bed"),
        (ALEX_CHORE_2, "Feed the cat"),
    ):
        state = _state(hass, entity_id)
        assert state.name == f"Alexander {title}"
        assert state.attributes["kid_name"] == "Alexander"

    assert _state(hass, ISABELLE_POINTS).name == "Isabelle weekly points"
    assert _state(hass, ISABELLE_CHORE_1).name == "Isabelle Make the bed"
    assert _state(hass, ISABELLE_CHORE_2).name == "Isabelle Feed the cat"


async def test_update_child_preserves_stable_ids_and_registry_identity(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test a child rename preserves all stable IDs and entity identities."""
    await _create_child_assignment(hass)

    entity_registry = er.async_get(hass)
    original_sensor_entry = entity_registry.async_get(ALEX_POINTS)
    original_switch_entry = entity_registry.async_get(ALEX_CHORE_1)
    assert original_sensor_entry is not None
    assert original_switch_entry is not None

    await _call_action(
        hass,
        "update_child",
        {
            "child_id": "kid_1",
            "name": "Alexander",
        },
    )

    store = loaded_config_entry.runtime_data
    assert store.data["children"] == {
        "kid_1": {
            "name": "Alexander",
            "active": True,
        }
    }
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert store.data["next_child_id"] == 2
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 2

    updated_sensor_entry = entity_registry.async_get(ALEX_POINTS)
    updated_switch_entry = entity_registry.async_get(ALEX_CHORE_1)
    assert updated_sensor_entry is not None
    assert updated_switch_entry is not None
    assert updated_sensor_entry.entity_id == original_sensor_entry.entity_id
    assert updated_sensor_entry.unique_id == original_sensor_entry.unique_id
    assert updated_sensor_entry.config_entry_id == original_sensor_entry.config_entry_id
    assert updated_switch_entry.entity_id == original_switch_entry.entity_id
    assert updated_switch_entry.unique_id == original_switch_entry.unique_id
    assert updated_switch_entry.config_entry_id == original_switch_entry.config_entry_id


async def test_update_child_preserves_completion_snapshot_and_earned_points(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test a rename does not rewrite completion history or earned points."""
    await _create_child_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])

    await _call_action(
        hass,
        "update_child",
        {
            "child_id": "kid_1",
            "name": "Alexander",
        },
    )

    assert store.data["completions"]["completion_1"] == completion
    assert completion["child_name"] == "Alex"
    assert completion["points"] == 2

    points_state = _state(hass, ALEX_POINTS)
    assert points_state.state == "2"
    assert points_state.name == "Alexander weekly points"
    assert points_state.attributes["kid_name"] == "Alexander"

    switch_state = _state(hass, ALEX_CHORE_1)
    assert switch_state.state == "on"
    assert switch_state.name == "Alexander Make the bed"
    assert switch_state.attributes["kid_name"] == "Alexander"


async def test_update_inactive_child_appears_after_reactivation(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test renaming an inactive child is reflected after reactivation."""
    await _create_child_assignment(hass)

    entity_registry = er.async_get(hass)
    original_sensor_entry = entity_registry.async_get(ALEX_POINTS)
    original_switch_entry = entity_registry.async_get(ALEX_CHORE_1)
    assert original_sensor_entry is not None
    assert original_switch_entry is not None

    await _call_action(
        hass,
        "set_child_active",
        {
            "child_id": "kid_1",
            "active": False,
        },
    )

    assert _state(hass, ALEX_POINTS).state == STATE_UNAVAILABLE
    inactive_switch = _state(hass, ALEX_CHORE_1)
    assert inactive_switch.state == STATE_UNAVAILABLE
    assert inactive_switch.attributes[ATTR_RESTORED] is True

    await _call_action(
        hass,
        "update_child",
        {
            "child_id": "kid_1",
            "name": "Alexander",
        },
    )
    await _call_action(
        hass,
        "set_child_active",
        {
            "child_id": "kid_1",
            "active": True,
        },
    )

    assert _state(hass, ALEX_POINTS).name == "Alexander weekly points"
    restored_switch = _state(hass, ALEX_CHORE_1)
    assert restored_switch.state == "off"
    assert restored_switch.name == "Alexander Make the bed"
    assert restored_switch.attributes["kid_name"] == "Alexander"
    assert ATTR_RESTORED not in restored_switch.attributes

    restored_sensor_entry = entity_registry.async_get(ALEX_POINTS)
    restored_switch_entry = entity_registry.async_get(ALEX_CHORE_1)
    assert restored_sensor_entry is not None
    assert restored_switch_entry is not None
    assert restored_sensor_entry.unique_id == original_sensor_entry.unique_id
    assert restored_switch_entry.unique_id == original_switch_entry.unique_id


async def test_update_child_is_idempotent(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test setting the current child name does not persist a change."""
    await _create_child_assignment(hass)

    store = loaded_config_entry.runtime_data

    with patch.object(store, "async_save", wraps=store.async_save) as async_save:
        await _call_action(
            hass,
            "update_child",
            {
                "child_id": "kid_1",
                "name": "  Alex  ",
            },
        )

    async_save.assert_not_awaited()
    assert store.data["children"]["kid_1"]["name"] == "Alex"
    assert store.data["next_child_id"] == 2
    assert store.data["next_assignment_id"] == 2
    assert _state(hass, ALEX_POINTS).name == "Alex weekly points"
    assert _state(hass, ALEX_CHORE_1).name == "Alex Make the bed"


async def test_update_child_rejects_unknown_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test child metadata updates reject an unknown stable child ID."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "update_child",
            {
                "child_id": "kid_999",
                "name": "Unknown child",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_child"
    assert exc_info.value.translation_placeholders == {"child_id": "kid_999"}
    assert loaded_config_entry.runtime_data.data["children"] == {}
