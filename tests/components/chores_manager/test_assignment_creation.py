"""Test creating assignments between existing children and chores."""

import pytest

from homeassistant.const import ATTR_ENTITY_ID
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
    entity_id: str,
) -> None:
    """Call a switch action and wait for Chores Manager updates."""
    await hass.services.async_call(
        "switch",
        action,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()


async def _create_existing_chore_and_later_child(hass: HomeAssistant) -> None:
    """Create a chore for Alex, then add Isabelle without that assignment."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
            "icon": "mdi:bed",
            "child_ids": ["kid_1"],
        },
    )
    await _call_action(hass, "add_child", {"name": "Isabelle"})


async def test_add_assignment_creates_stable_switch_and_label(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assigning an existing chore to a child added later."""
    await _create_existing_chore_and_later_child(hass)

    assert hass.states.get(ISABELLE_SWITCH) is None

    await _call_action(
        hass,
        "add_assignment",
        {
            "child_id": "kid_2",
            "chore_id": "chore_1",
        },
    )

    store = loaded_config_entry.runtime_data
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_1",
            "chore_id": "chore_1",
            "active": True,
        },
        "assignment_2": {
            "child_id": "kid_2",
            "chore_id": "chore_1",
            "active": True,
        },
    }
    assert store.data["next_assignment_id"] == 3

    state = _state(hass, ISABELLE_SWITCH)
    assert state.state == "off"
    assert state.name == "Isabelle Make the bed"
    assert state.attributes["assignment_id"] == "assignment_2"
    assert state.attributes["child_id"] == "kid_2"
    assert state.attributes["chore_id"] == "chore_1"
    assert state.attributes["points"] == 2

    entity_registry = er.async_get(hass)
    registry_entry = entity_registry.async_get(ISABELLE_SWITCH)
    assert registry_entry is not None
    assert registry_entry.unique_id == "assignment_2"

    label_registry = lr.async_get(hass)
    chores_label = label_registry.async_get_label_by_name("Chores")
    assert chores_label is not None
    assert chores_label.label_id in registry_entry.labels
    assert store.data["label_initialized_assignment_ids"] == [
        "assignment_1",
        "assignment_2",
    ]


async def test_added_assignment_completes_independently_and_preserves_history(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test a new assignment can complete without changing existing history."""
    await _create_existing_chore_and_later_child(hass)
    await _call_switch_action(hass, "turn_on", ALEX_SWITCH)

    store = loaded_config_entry.runtime_data
    alex_completion = dict(store.data["completions"]["completion_1"])

    await _call_action(
        hass,
        "add_assignment",
        {
            "child_id": "kid_2",
            "chore_id": "chore_1",
        },
    )
    await _call_switch_action(hass, "turn_on", ISABELLE_SWITCH)

    assert _state(hass, ALEX_SWITCH).state == "on"
    assert _state(hass, ISABELLE_SWITCH).state == "on"
    assert _state(hass, ALEX_POINTS).state == "2"
    assert _state(hass, ISABELLE_POINTS).state == "2"

    assert store.data["completions"]["completion_1"] == alex_completion
    assert store.data["completions"]["completion_2"]["assignment_id"] == (
        "assignment_2"
    )
    assert store.data["completions"]["completion_2"]["child_id"] == "kid_2"
    assert store.data["completions"]["completion_2"]["chore_id"] == "chore_1"


async def test_add_assignment_rejects_existing_active_relationship(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test duplicate active child-to-chore relationships are rejected."""
    await _create_existing_chore_and_later_child(hass)

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_assignment",
            {
                "child_id": "kid_1",
                "chore_id": "chore_1",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "duplicate_assignment"
    assert exc_info.value.translation_placeholders == {
        "assignment_id": "assignment_1",
        "child_id": "kid_1",
        "chore_id": "chore_1",
    }

    store = loaded_config_entry.runtime_data
    assert list(store.data["assignments"]) == ["assignment_1"]
    assert store.data["next_assignment_id"] == 2


async def test_add_assignment_rejects_existing_inactive_relationship(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test an inactive relationship must be reactivated instead of recreated."""
    await _create_existing_chore_and_later_child(hass)
    await _call_action(
        hass,
        "set_assignment_active",
        {
            "assignment_id": "assignment_1",
            "active": False,
        },
    )

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_assignment",
            {
                "child_id": "kid_1",
                "chore_id": "chore_1",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "duplicate_assignment"
    assert exc_info.value.translation_placeholders == {
        "assignment_id": "assignment_1",
        "child_id": "kid_1",
        "chore_id": "chore_1",
    }

    store = loaded_config_entry.runtime_data
    assert store.data["assignments"]["assignment_1"]["active"] is False
    assert store.data["next_assignment_id"] == 2


async def test_add_assignment_rejects_unknown_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment creation rejects an unknown child ID."""
    await _create_existing_chore_and_later_child(hass)

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_assignment",
            {
                "child_id": "kid_999",
                "chore_id": "chore_1",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_child"
    assert exc_info.value.translation_placeholders == {"child_id": "kid_999"}
    assert loaded_config_entry.runtime_data.data["next_assignment_id"] == 2


async def test_add_assignment_rejects_unknown_chore(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment creation rejects an unknown chore ID."""
    await _call_action(hass, "add_child", {"name": "Alex"})

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_assignment",
            {
                "child_id": "kid_1",
                "chore_id": "chore_999",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_chore"
    assert exc_info.value.translation_placeholders == {"chore_id": "chore_999"}
    assert loaded_config_entry.runtime_data.data["assignments"] == {}


async def test_add_assignment_rejects_inactive_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment creation requires an active child."""
    await _create_existing_chore_and_later_child(hass)
    await _call_action(
        hass,
        "set_child_active",
        {
            "child_id": "kid_2",
            "active": False,
        },
    )

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_assignment",
            {
                "child_id": "kid_2",
                "chore_id": "chore_1",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "inactive_child"
    assert exc_info.value.translation_placeholders == {"child_id": "kid_2"}

    store = loaded_config_entry.runtime_data
    assert list(store.data["assignments"]) == ["assignment_1"]
    assert store.data["next_assignment_id"] == 2


async def test_add_assignment_rejects_inactive_chore(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment creation requires an active chore."""
    await _create_existing_chore_and_later_child(hass)
    await _call_action(
        hass,
        "set_chore_active",
        {
            "chore_id": "chore_1",
            "active": False,
        },
    )

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_assignment",
            {
                "child_id": "kid_2",
                "chore_id": "chore_1",
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "inactive_chore"
    assert exc_info.value.translation_placeholders == {"chore_id": "chore_1"}

    store = loaded_config_entry.runtime_data
    assert list(store.data["assignments"]) == ["assignment_1"]
    assert store.data["next_assignment_id"] == 2
