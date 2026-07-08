"""Test Chores Manager child activation lifecycle."""

import pytest

from homeassistant.const import ATTR_ENTITY_ID, ATTR_RESTORED, STATE_UNAVAILABLE
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


async def _create_child_assignment(hass: HomeAssistant) -> None:
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


async def test_deactivate_child_makes_entities_unavailable_and_preserves_history(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test deactivation preserves stable data and completion history."""
    await _create_child_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])

    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_1", "active": False},
    )

    points_state = _state(hass, ALEX_POINTS)
    assert points_state.state == STATE_UNAVAILABLE
    assert ATTR_RESTORED not in points_state.attributes

    switch_state = _state(hass, ALEX_SWITCH)
    assert switch_state.state == STATE_UNAVAILABLE
    assert switch_state.attributes[ATTR_RESTORED] is True

    assert store.data["children"]["kid_1"] == {
        "name": "Alex",
        "active": False,
    }
    assert store.data["assignments"]["assignment_1"] == {
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "active": True,
    }
    assert store.data["completions"]["completion_1"] == completion
    assert store.get_current_week_points("kid_1") == 2


async def test_reactivate_child_restores_same_entities_and_completion(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test reactivation restores the same entities and today's completion."""
    await _create_child_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    entity_registry = er.async_get(hass)
    original_sensor_entry = entity_registry.async_get(ALEX_POINTS)
    original_switch_entry = entity_registry.async_get(ALEX_SWITCH)
    assert original_sensor_entry is not None
    assert original_switch_entry is not None

    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_1", "active": False},
    )
    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_1", "active": True},
    )

    assert _state(hass, ALEX_POINTS).state == "2"
    restored_switch = _state(hass, ALEX_SWITCH)
    assert restored_switch.state == "on"
    assert ATTR_RESTORED not in restored_switch.attributes

    restored_sensor_entry = entity_registry.async_get(ALEX_POINTS)
    restored_switch_entry = entity_registry.async_get(ALEX_SWITCH)
    assert restored_sensor_entry is not None
    assert restored_switch_entry is not None
    assert restored_sensor_entry.unique_id == original_sensor_entry.unique_id
    assert restored_sensor_entry.entity_id == original_sensor_entry.entity_id
    assert restored_switch_entry.unique_id == original_switch_entry.unique_id
    assert restored_switch_entry.entity_id == original_switch_entry.entity_id

    store = loaded_config_entry.runtime_data
    assert store.data["next_child_id"] == 2
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 2
    assert list(store.data["completions"]) == ["completion_1"]


async def test_set_child_active_is_idempotent(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test repeated activation changes do not duplicate or lose entities."""
    await _create_child_assignment(hass)

    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_1", "active": True},
    )
    assert _state(hass, ALEX_POINTS).state == "0"
    assert _state(hass, ALEX_SWITCH).state == "off"

    for _ in range(2):
        await _call_action(
            hass,
            "set_child_active",
            {"child_id": "kid_1", "active": False},
        )
        assert _state(hass, ALEX_POINTS).state == STATE_UNAVAILABLE
        assert _state(hass, ALEX_SWITCH).state == STATE_UNAVAILABLE

    for _ in range(2):
        await _call_action(
            hass,
            "set_child_active",
            {"child_id": "kid_1", "active": True},
        )
        assert _state(hass, ALEX_POINTS).state == "0"
        assert _state(hass, ALEX_SWITCH).state == "off"

    store = loaded_config_entry.runtime_data
    assert store.data["children"] == {"kid_1": {"name": "Alex", "active": True}}
    assert list(store.data["assignments"]) == ["assignment_1"]
    assert store.data["next_child_id"] == 2
    assert store.data["next_assignment_id"] == 2


async def test_set_child_active_rejects_unknown_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test activation rejects an unknown stable child ID."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "set_child_active",
            {"child_id": "kid_999", "active": False},
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_child"
    assert exc_info.value.translation_placeholders == {"child_id": "kid_999"}
    assert loaded_config_entry.runtime_data.data["children"] == {}


async def test_deactivate_child_only_affects_that_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test deactivation leaves another child's entities operational."""
    await _create_two_child_assignment(hass)
    await _call_switch_action(hass, "turn_on", ISABELLE_SWITCH)

    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_1", "active": False},
    )

    assert _state(hass, ALEX_POINTS).state == STATE_UNAVAILABLE
    assert _state(hass, ALEX_SWITCH).state == STATE_UNAVAILABLE
    assert _state(hass, ISABELLE_POINTS).state == "2"
    assert _state(hass, ISABELLE_SWITCH).state == "on"

    store = loaded_config_entry.runtime_data
    assert store.data["children"]["kid_1"]["active"] is False
    assert store.data["children"]["kid_2"]["active"] is True
    assert store.get_current_week_points("kid_1") == 0
    assert store.get_current_week_points("kid_2") == 2


async def test_new_chore_skips_inactive_children(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test default assignment only includes children that remain active."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(hass, "add_child", {"name": "Isabelle"})
    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_1", "active": False},
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

    store = loaded_config_entry.runtime_data
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_2",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert hass.states.get("switch.kid_1_chore_1") is None
    assert _state(hass, "switch.kid_2_chore_1").state == "off"
