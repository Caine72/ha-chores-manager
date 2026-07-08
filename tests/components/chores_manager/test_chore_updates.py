"""Test Chores Manager chore metadata updates."""

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


async def _create_assignment(
    hass: HomeAssistant,
    *,
    two_children: bool = False,
) -> None:
    """Create a chore assigned to one or two children."""
    await _call_action(hass, "add_child", {"name": "Alex"})

    if two_children:
        await _call_action(hass, "add_child", {"name": "Isabelle"})

    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
            "icon": "mdi:bed",
            "sort_order": 10,
        },
    )


async def test_update_chore_partially_updates_live_metadata(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test a partial update changes only the requested chore field."""
    await _create_assignment(hass)

    await _call_action(
        hass,
        "update_chore",
        {
            "chore_id": "chore_1",
            "title": "  Make the bed properly  ",
        },
    )

    store = loaded_config_entry.runtime_data
    assert store.data["chores"]["chore_1"] == {
        "title": "Make the bed properly",
        "category": "Morning",
        "points": 2,
        "icon": "mdi:bed",
        "active": True,
        "sort_order": 10,
        "completion_mode": "independent",
    }

    state = _state(hass, ALEX_SWITCH)
    assert state.state == "off"
    assert state.name == "Alex Make the bed properly"
    assert state.attributes["title"] == "Make the bed properly"
    assert state.attributes["category"] == "Morning"
    assert state.attributes["points"] == 2


async def test_update_chore_updates_all_editable_fields(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test updating all editable chore metadata together."""
    await _create_assignment(hass)

    await _call_action(
        hass,
        "update_chore",
        {
            "chore_id": "chore_1",
            "title": "Clean the bedroom",
            "category": "Cleaning",
            "points": 5,
            "icon": "mdi:broom",
            "sort_order": 25,
        },
    )

    store = loaded_config_entry.runtime_data
    assert store.data["chores"]["chore_1"] == {
        "title": "Clean the bedroom",
        "category": "Cleaning",
        "points": 5,
        "icon": "mdi:broom",
        "active": True,
        "sort_order": 25,
        "completion_mode": "independent",
    }

    state = _state(hass, ALEX_SWITCH)
    assert state.name == "Alex Clean the bedroom"
    assert state.attributes["title"] == "Clean the bedroom"
    assert state.attributes["category"] == "Cleaning"
    assert state.attributes["points"] == 5
    assert state.attributes["sort_order"] == 25
    assert state.attributes["icon"] == "mdi:broom"


async def test_update_chore_preserves_stable_ids_and_registry_identity(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test metadata updates preserve chore, assignment, and entity identity."""
    await _create_assignment(hass)

    entity_registry = er.async_get(hass)
    original_entry = entity_registry.async_get(ALEX_SWITCH)
    assert original_entry is not None

    await _call_action(
        hass,
        "update_chore",
        {
            "chore_id": "chore_1",
            "points": 4,
        },
    )

    store = loaded_config_entry.runtime_data
    assert list(store.data["chores"]) == ["chore_1"]
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        }
    }
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 2

    updated_entry = entity_registry.async_get(ALEX_SWITCH)
    assert updated_entry is not None
    assert updated_entry.entity_id == original_entry.entity_id == ALEX_SWITCH
    assert updated_entry.unique_id == original_entry.unique_id == "assignment_1"
    assert updated_entry.config_entry_id == original_entry.config_entry_id


async def test_update_chore_preserves_completion_snapshot_and_earned_points(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test updates affect future metadata but not an earned completion."""
    await _create_assignment(hass)
    await _call_switch_action(hass, "turn_on")

    store = loaded_config_entry.runtime_data
    completion = dict(store.data["completions"]["completion_1"])

    await _call_action(
        hass,
        "update_chore",
        {
            "chore_id": "chore_1",
            "title": "Make the bed properly",
            "points": 5,
        },
    )

    assert store.data["completions"]["completion_1"] == completion
    assert completion["chore_title"] == "Make the bed"
    assert completion["points"] == 2
    assert _state(hass, ALEX_POINTS).state == "2"

    state = _state(hass, ALEX_SWITCH)
    assert state.state == "on"
    assert state.name == "Alex Make the bed properly"
    assert state.attributes["title"] == "Make the bed properly"
    assert state.attributes["points"] == 5


async def test_update_chore_refreshes_all_child_assignments(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test one chore update refreshes every assignment entity."""
    await _create_assignment(hass, two_children=True)

    await _call_action(
        hass,
        "update_chore",
        {
            "chore_id": "chore_1",
            "title": "Tidy the bedroom",
            "category": "Cleaning",
            "points": 4,
        },
    )

    alex_state = _state(hass, ALEX_SWITCH)
    isabelle_state = _state(hass, ISABELLE_SWITCH)

    assert alex_state.name == "Alex Tidy the bedroom"
    assert isabelle_state.name == "Isabelle Tidy the bedroom"

    for state in (alex_state, isabelle_state):
        assert state.attributes["chore_id"] == "chore_1"
        assert state.attributes["title"] == "Tidy the bedroom"
        assert state.attributes["category"] == "Cleaning"
        assert state.attributes["points"] == 4

    store = loaded_config_entry.runtime_data
    assert list(store.data["assignments"]) == [
        "assignment_1",
        "assignment_2",
    ]


async def test_update_inactive_chore_appears_after_reactivation(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test inactive chore metadata is used when its entity returns."""
    await _create_assignment(hass)

    entity_registry = er.async_get(hass)
    original_entry = entity_registry.async_get(ALEX_SWITCH)
    assert original_entry is not None

    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": False},
    )

    inactive_state = _state(hass, ALEX_SWITCH)
    assert inactive_state.state == STATE_UNAVAILABLE
    assert inactive_state.attributes[ATTR_RESTORED] is True

    await _call_action(
        hass,
        "update_chore",
        {
            "chore_id": "chore_1",
            "title": "Tidy the bedroom",
            "icon": "mdi:broom",
        },
    )
    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": True},
    )

    restored_state = _state(hass, ALEX_SWITCH)
    assert restored_state.state == "off"
    assert restored_state.name == "Alex Tidy the bedroom"
    assert restored_state.attributes["title"] == "Tidy the bedroom"
    assert restored_state.attributes["icon"] == "mdi:broom"
    assert ATTR_RESTORED not in restored_state.attributes

    restored_entry = entity_registry.async_get(ALEX_SWITCH)
    assert restored_entry is not None
    assert restored_entry.entity_id == original_entry.entity_id
    assert restored_entry.unique_id == original_entry.unique_id == "assignment_1"


async def test_update_chore_rejects_unknown_chore(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test metadata updates reject an unknown stable chore ID."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "update_chore",
            {
                "chore_id": "chore_999",
                "title": "Unknown chore",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_chore"
    assert exc_info.value.translation_placeholders == {"chore_id": "chore_999"}
    assert loaded_config_entry.runtime_data.data["chores"] == {}


async def test_update_chore_rejects_empty_update(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test an update must contain at least one editable field."""
    await _create_assignment(hass)

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "update_chore",
            {"chore_id": "chore_1"},
            blocking=True,
        )

    assert exc_info.value.translation_key == "no_chore_updates"
    assert loaded_config_entry.runtime_data.data["chores"]["chore_1"]["title"] == (
        "Make the bed"
    )
