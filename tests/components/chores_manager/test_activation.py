"""Test Chores Manager chore activation lifecycle."""

import pytest

from homeassistant.const import ATTR_ENTITY_ID, ATTR_RESTORED, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er, label_registry as lr

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


async def test_deactivate_chore_makes_switch_unavailable_and_preserves_history(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test deactivation unloads the live entity without deleting history."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])

    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": False},
    )

    inactive_state = _state(hass, CHORE_SWITCH)
    assert inactive_state.state == STATE_UNAVAILABLE
    assert inactive_state.attributes[ATTR_RESTORED] is True
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"

    assert store.data["chores"]["chore_1"]["active"] is False
    assert store.data["assignments"]["assignment_1"] == {
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "active": True,
    }
    assert store.data["completions"]["completion_1"] == completion

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(CHORE_SWITCH)
    assert registry_entry is not None
    assert registry_entry.unique_id == "assignment_1"


async def test_reactivate_chore_restores_same_entity_and_completion(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test reactivation restores the same entity and today's completion."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    entity_registry = er.async_get(hass)
    original_entry = entity_registry.async_get(CHORE_SWITCH)
    assert original_entry is not None

    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": False},
    )
    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": True},
    )

    restored_state = _state(hass, CHORE_SWITCH)
    assert restored_state.state == "on"
    assert ATTR_RESTORED not in restored_state.attributes
    assert restored_state.attributes["assignment_id"] == "assignment_1"

    restored_entry = entity_registry.async_get(CHORE_SWITCH)
    assert restored_entry is not None
    assert restored_entry.unique_id == original_entry.unique_id == "assignment_1"
    assert restored_entry.entity_id == original_entry.entity_id == CHORE_SWITCH
    assert restored_entry.config_entry_id == original_entry.config_entry_id

    store = loaded_config_entry.runtime_data
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 2
    assert list(store.data["completions"]) == ["completion_1"]
    assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"


async def test_set_chore_active_is_idempotent(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test repeated activation changes do not duplicate or lose entities."""
    await _create_assignment(hass)

    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": True},
    )
    assert _state(hass, CHORE_SWITCH).state == "off"

    for _ in range(2):
        await _call_action(
            hass,
            "set_chore_active",
            {"chore_id": "chore_1", "active": False},
        )
        inactive_state = _state(hass, CHORE_SWITCH)
        assert inactive_state.state == STATE_UNAVAILABLE
        assert inactive_state.attributes[ATTR_RESTORED] is True

    for _ in range(2):
        await _call_action(
            hass,
            "set_chore_active",
            {"chore_id": "chore_1", "active": True},
        )
        assert _state(hass, CHORE_SWITCH).state == "off"

    store = loaded_config_entry.runtime_data
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 2
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        }
    }

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(CHORE_SWITCH)
    assert registry_entry is not None
    assert registry_entry.unique_id == "assignment_1"


async def test_set_chore_active_rejects_unknown_chore(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test activation rejects an unknown stable chore ID."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "set_chore_active",
            {"chore_id": "chore_999", "active": False},
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_chore"
    assert exc_info.value.translation_placeholders == {"chore_id": "chore_999"}
    assert loaded_config_entry.runtime_data.data["chores"] == {}


async def test_reactivation_preserves_assignment_labels(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test reactivation preserves integration and user-managed labels."""
    await _create_assignment(hass)

    store = loaded_config_entry.runtime_data
    assert store.data["label_initialized_assignment_ids"] == ["assignment_1"]

    label_registry = lr.async_get(hass)
    chores_label = label_registry.async_get_label_by_name("Chores")
    assert chores_label is not None
    family_label = label_registry.async_create("Family")

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(CHORE_SWITCH)
    assert registry_entry is not None
    assert chores_label.label_id in registry_entry.labels

    entity_registry.async_update_entity(
        CHORE_SWITCH,
        labels={chores_label.label_id, family_label.label_id},
    )

    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": False},
    )
    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": True},
    )

    restored_entry = entity_registry.async_get(CHORE_SWITCH)
    assert restored_entry is not None
    assert restored_entry.labels == {chores_label.label_id, family_label.label_id}
    assert store.data["label_initialized_assignment_ids"] == ["assignment_1"]
