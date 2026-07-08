"""Test Chores Manager assignment activation lifecycle."""

import pytest

from homeassistant.const import ATTR_ENTITY_ID, ATTR_RESTORED, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er, label_registry as lr

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


async def test_deactivate_assignment_makes_switch_unavailable_and_preserves_history(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment deactivation preserves stable data and history."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])

    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": False},
    )

    switch_state = _state(hass, ALEX_SWITCH)
    assert switch_state.state == STATE_UNAVAILABLE
    assert switch_state.attributes[ATTR_RESTORED] is True
    assert _state(hass, ALEX_POINTS).state == "2"

    assert store.data["children"]["kid_1"]["active"] is True
    assert store.data["chores"]["chore_1"]["active"] is True
    assert store.data["assignments"]["assignment_1"] == {
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "active": False,
    }
    assert store.data["completions"]["completion_1"] == completion
    assert store.get_current_week_points("kid_1") == 2

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(ALEX_SWITCH)
    assert registry_entry is not None
    assert registry_entry.unique_id == "assignment_1"


async def test_reactivate_assignment_restores_same_entity_and_completion(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment reactivation restores identity and completion state."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    entity_registry = er.async_get(hass)
    original_entry = entity_registry.async_get(ALEX_SWITCH)
    assert original_entry is not None

    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": False},
    )
    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": True},
    )

    restored_state = _state(hass, ALEX_SWITCH)
    assert restored_state.state == "on"
    assert ATTR_RESTORED not in restored_state.attributes
    assert restored_state.attributes["assignment_id"] == "assignment_1"

    restored_entry = entity_registry.async_get(ALEX_SWITCH)
    assert restored_entry is not None
    assert restored_entry.entity_id == original_entry.entity_id == ALEX_SWITCH
    assert restored_entry.unique_id == original_entry.unique_id == "assignment_1"
    assert restored_entry.config_entry_id == original_entry.config_entry_id

    store = loaded_config_entry.runtime_data
    assert store.data["next_assignment_id"] == 2
    assert list(store.data["completions"]) == ["completion_1"]
    assert _state(hass, ALEX_POINTS).state == "2"


async def test_set_assignment_active_is_idempotent(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test repeated assignment activation changes preserve identity."""
    await _create_assignment(hass)

    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": True},
    )
    assert _state(hass, ALEX_SWITCH).state == "off"

    for _ in range(2):
        await _call_action(
            hass,
            "set_assignment_active",
            {"assignment_id": "assignment_1", "active": False},
        )
        inactive_state = _state(hass, ALEX_SWITCH)
        assert inactive_state.state == STATE_UNAVAILABLE
        assert inactive_state.attributes[ATTR_RESTORED] is True

    for _ in range(2):
        await _call_action(
            hass,
            "set_assignment_active",
            {"assignment_id": "assignment_1", "active": True},
        )
        assert _state(hass, ALEX_SWITCH).state == "off"

    store = loaded_config_entry.runtime_data
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert store.data["next_assignment_id"] == 2

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(ALEX_SWITCH)
    assert registry_entry is not None
    assert registry_entry.unique_id == "assignment_1"


async def test_set_assignment_active_rejects_unknown_assignment(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test activation rejects an unknown stable assignment ID."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "set_assignment_active",
            {"assignment_id": "assignment_999", "active": False},
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_assignment"
    assert exc_info.value.translation_placeholders == {
        "assignment_id": "assignment_999"
    }
    assert loaded_config_entry.runtime_data.data["assignments"] == {}


async def test_deactivate_assignment_only_affects_selected_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test one assignment can be disabled without affecting another child."""
    await _create_two_child_assignment(hass)
    await _call_switch_action(hass, "turn_on", ISABELLE_SWITCH)

    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": False},
    )

    assert _state(hass, ALEX_SWITCH).state == STATE_UNAVAILABLE
    assert _state(hass, ALEX_POINTS).state == "0"
    assert _state(hass, ISABELLE_SWITCH).state == "on"
    assert _state(hass, ISABELLE_POINTS).state == "2"

    store = loaded_config_entry.runtime_data
    assert store.data["assignments"]["assignment_1"]["active"] is False
    assert store.data["assignments"]["assignment_2"]["active"] is True
    assert store.data["children"]["kid_1"]["active"] is True
    assert store.data["children"]["kid_2"]["active"] is True
    assert store.data["chores"]["chore_1"]["active"] is True


async def test_assignment_reactivation_preserves_labels(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment reactivation preserves integration and user labels."""
    await _create_assignment(hass)

    store = loaded_config_entry.runtime_data
    assert store.data["label_initialized_assignment_ids"] == ["assignment_1"]

    label_registry = lr.async_get(hass)
    chores_label = label_registry.async_get_label_by_name("Chores")
    assert chores_label is not None
    family_label = label_registry.async_create("Family")

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(ALEX_SWITCH)
    assert registry_entry is not None
    assert chores_label.label_id in registry_entry.labels

    entity_registry.async_update_entity(
        ALEX_SWITCH,
        labels={chores_label.label_id, family_label.label_id},
    )

    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": False},
    )
    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": True},
    )

    restored_entry = entity_registry.async_get(ALEX_SWITCH)
    assert restored_entry is not None
    assert restored_entry.labels == {chores_label.label_id, family_label.label_id}
    assert store.data["label_initialized_assignment_ids"] == ["assignment_1"]
