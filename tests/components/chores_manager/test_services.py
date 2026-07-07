"""Test Chores Manager actions and dynamic entity creation."""

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .common import DOMAIN

from tests.common import MockConfigEntry


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


async def test_add_children_creates_stable_sensors(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test adding children and creating their weekly-points sensors."""
    await _call_action(hass, "add_child", {"name": "  Alex  "})
    await _call_action(hass, "add_child", {"name": "Isabelle"})

    store = loaded_config_entry.runtime_data
    assert store.data["children"] == {
        "kid_1": {"name": "Alex", "active": True},
        "kid_2": {"name": "Isabelle", "active": True},
    }
    assert store.data["next_child_id"] == 3

    alex_state = hass.states.get("sensor.kid_1_weekly_points")
    assert alex_state is not None
    assert alex_state.state == "0"
    assert alex_state.name == "Alex weekly points"
    assert alex_state.attributes["child_id"] == "kid_1"
    assert alex_state.attributes["kid_name"] == "Alex"

    isabelle_state = hass.states.get("sensor.kid_2_weekly_points")
    assert isabelle_state is not None
    assert isabelle_state.state == "0"
    assert isabelle_state.name == "Isabelle weekly points"

    entity_registry = er.async_get(hass)
    alex_entry = entity_registry.async_get("sensor.kid_1_weekly_points")
    assert alex_entry is not None
    assert alex_entry.unique_id == "kid_1_weekly_points"

    isabelle_entry = entity_registry.async_get("sensor.kid_2_weekly_points")
    assert isabelle_entry is not None
    assert isabelle_entry.unique_id == "kid_2_weekly_points"


async def test_add_chore_assigns_all_active_children(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test that omitting child IDs assigns a chore to every active child."""
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

    store = loaded_config_entry.runtime_data
    assert store.data["chores"] == {
        "chore_1": {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
            "icon": "mdi:checkbox-marked-circle-outline",
            "active": True,
            "sort_order": 10,
            "completion_mode": "independent",
        }
    }
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
    assert store.data["next_chore_id"] == 2
    assert store.data["next_assignment_id"] == 3

    alex_switch = hass.states.get("switch.kid_1_chore_1")
    assert alex_switch is not None
    assert alex_switch.state == "off"
    assert alex_switch.name == "Alex Make the bed"
    assert alex_switch.attributes["assignment_id"] == "assignment_1"
    assert alex_switch.attributes["child_id"] == "kid_1"
    assert alex_switch.attributes["chore_id"] == "chore_1"
    assert alex_switch.attributes["points"] == 2
    assert alex_switch.attributes["completion_mode"] == "independent"

    isabelle_switch = hass.states.get("switch.kid_2_chore_1")
    assert isabelle_switch is not None
    assert isabelle_switch.state == "off"
    assert isabelle_switch.name == "Isabelle Make the bed"

    entity_registry = er.async_get(hass)
    alex_entry = entity_registry.async_get("switch.kid_1_chore_1")
    assert alex_entry is not None
    assert alex_entry.unique_id == "assignment_1"

    isabelle_entry = entity_registry.async_get("switch.kid_2_chore_1")
    assert isabelle_entry is not None
    assert isabelle_entry.unique_id == "assignment_2"


async def test_add_chore_targets_selected_children_once(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test explicit child selection and duplicate child-ID removal."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(hass, "add_child", {"name": "Isabelle"})
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Feed the cat",
            "category": "Evening",
            "points": 3,
            "icon": "mdi:cat",
            "sort_order": 25,
            "child_ids": ["kid_2", "kid_2"],
        },
    )

    store = loaded_config_entry.runtime_data
    assert store.data["chores"]["chore_1"] == {
        "title": "Feed the cat",
        "category": "Evening",
        "points": 3,
        "icon": "mdi:cat",
        "active": True,
        "sort_order": 25,
        "completion_mode": "independent",
    }
    assert store.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_2",
            "chore_id": "chore_1",
            "active": True,
        }
    }

    assert hass.states.get("switch.kid_1_chore_1") is None
    assert hass.states.get("switch.kid_2_chore_1") is not None


async def test_add_chore_requires_active_children(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test adding a default-assigned chore without active children."""
    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_chore",
            {
                "title": "Make the bed",
                "category": "Morning",
                "points": 2,
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "no_active_children"
    assert loaded_config_entry.runtime_data.data["chores"] == {}


async def test_add_chore_rejects_unknown_children(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assigning a chore to an unknown child."""
    await _call_action(hass, "add_child", {"name": "Alex"})

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_chore",
            {
                "title": "Make the bed",
                "category": "Morning",
                "points": 2,
                "child_ids": ["kid_999"],
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "unknown_children"
    assert exc_info.value.translation_placeholders == {"child_ids": "kid_999"}
    assert loaded_config_entry.runtime_data.data["chores"] == {}


async def test_add_chore_rejects_inactive_children(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assigning a chore to an inactive child."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    loaded_config_entry.runtime_data.data["children"]["kid_1"]["active"] = False

    with pytest.raises(ServiceValidationError) as exc_info:
        await hass.services.async_call(
            DOMAIN,
            "add_chore",
            {
                "title": "Make the bed",
                "category": "Morning",
                "points": 2,
                "child_ids": ["kid_1"],
            },
            blocking=True,
        )

    assert exc_info.value.translation_key == "inactive_children"
    assert exc_info.value.translation_placeholders == {"child_ids": "kid_1"}
    assert loaded_config_entry.runtime_data.data["chores"] == {}
