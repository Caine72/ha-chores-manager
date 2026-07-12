"""Test Chores Manager native management options flow."""

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from .common import DOMAIN

from tests.common import MockConfigEntry


async def _select_menu_option(
    hass: HomeAssistant,
    flow_id: str,
    next_step_id: str,
) -> ConfigFlowResult:
    """Select an options-flow menu item."""
    return await hass.config_entries.options.async_configure(
        flow_id,
        user_input={"next_step_id": next_step_id},
    )


async def test_options_flow_manages_child_lifecycle(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test the options flow manages child lifecycle through actions."""
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "children_menu"

    result = await _select_menu_option(hass, result["flow_id"], "init")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_child")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_child"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Alex"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "children_menu"
    assert loaded_config_entry.runtime_data.data["children"]["kid_1"] == {
        "name": "Alex",
        "active": True,
    }

    result = await _select_menu_option(hass, result["flow_id"], "select_child")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_child"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"child_id": "kid_1"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "child_actions"

    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "children_menu"

    result = await _select_menu_option(hass, result["flow_id"], "select_child")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"child_id": "kid_1"},
    )
    result = await _select_menu_option(hass, result["flow_id"], "edit_child")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit_child"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Alexandra"},
    )
    assert result["type"] is FlowResultType.MENU
    assert (
        loaded_config_entry.runtime_data.data["children"]["kid_1"]["name"]
        == "Alexandra"
    )

    result = await _select_menu_option(hass, result["flow_id"], "deactivate_child")
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["children"]["kid_1"]["active"] is False

    result = await _select_menu_option(hass, result["flow_id"], "delete_child")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "delete_child"

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["children"] == {}


async def test_options_flow_manages_chore_lifecycle(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test the options flow manages chore lifecycle through actions."""
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Isabelle"},
        blocking=True,
    )

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "chores_menu")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "chores_menu"

    result = await _select_menu_option(hass, result["flow_id"], "add_chore")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_chore"
    child_ids_key = next(
        key for key in result["data_schema"].schema if key.schema == "child_ids"
    )
    child_selector = result["data_schema"].schema[child_ids_key]
    assert child_ids_key.default() == ["kid_1", "kid_2"]
    assert child_selector.config["options"] == [
        {"value": "kid_1", "label": "Alex (kid_1)"},
        {"value": "kid_2", "label": "Isabelle (kid_2)"},
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
            "child_ids": ["kid_2"],
            "advanced_chore_options": {"icon": "mdi:bed"},
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["chores"]["chore_1"] == {
        "title": "Make the bed",
        "category": "Morning",
        "points": 2,
        "icon": "mdi:bed",
        "active": True,
        "sort_order": 10,
        "completion_mode": "independent",
    }
    assert loaded_config_entry.runtime_data.data["assignments"] == {
        "assignment_1": {
            "child_id": "kid_2",
            "chore_id": "chore_1",
            "active": True,
        }
    }

    result = await _select_menu_option(hass, result["flow_id"], "select_chore")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_chore"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"chore_id": "chore_1"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "chore_actions"
    assert result["description_placeholders"] == {
        "title": "Make the bed",
        "category": "Morning",
        "points": "2",
        "chore_id": "chore_1",
        "status": "Active",
    }

    result = await _select_menu_option(hass, result["flow_id"], "edit_chore")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "edit_chore"

    category_key = next(
        key for key in result["data_schema"].schema if key.schema == "category"
    )
    category_selector = result["data_schema"].schema[category_key]
    assert category_selector.config["options"] == ["Morning"]
    assert category_selector.config["custom_value"] is True

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "title": "Make the bed",
            "category": "Morning",
            "points": 3,
            "advanced_chore_options": {
                "icon": "mdi:bed",
                "sort_order": 20,
            },
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["chores"]["chore_1"]["points"] == 3
    assert (
        loaded_config_entry.runtime_data.data["chores"]["chore_1"]["sort_order"] == 20
    )

    result = await _select_menu_option(hass, result["flow_id"], "deactivate_chore")
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["chores"]["chore_1"]["active"] is False

    result = await _select_menu_option(hass, result["flow_id"], "delete_chore")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "delete_chore"

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["chores"] == {}
    assert loaded_config_entry.runtime_data.data["assignments"] == {}


async def test_options_flow_add_chore_requires_active_child(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test the options flow requires at least one selected active child."""
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "chores_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_chore")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
            "advanced_chore_options": {"icon": "mdi:bed"},
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_chore"
    assert result["errors"] == {"base": "no_children_selected"}


async def test_options_flow_manages_assignment_lifecycle(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test guided assignment creation and lifecycle management."""
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
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
    await hass.services.async_call(
        DOMAIN,
        "add_chore",
        {
            "title": "Feed the cat",
            "category": "Evening",
            "points": 3,
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Isabelle"},
        blocking=True,
    )

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "assignments_menu"

    result = await _select_menu_option(hass, result["flow_id"], "init")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_assignment_child")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_assignment_child"
    child_key = next(
        key for key in result["data_schema"].schema if key.schema == "child_id"
    )
    child_selector = result["data_schema"].schema[child_key]
    assert child_selector.config["options"] == [
        {"value": "kid_2", "label": "Isabelle (kid_2)"}
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"child_id": "kid_2"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_assignment_chore"
    assert result["description_placeholders"] == {"name": "Isabelle"}
    chore_key = next(
        key for key in result["data_schema"].schema if key.schema == "chore_ids"
    )
    chore_selector = result["data_schema"].schema[chore_key]
    assert chore_selector.config["options"] == [
        {
            "value": "chore_1",
            "label": "Make the bed (Morning, 2 points, chore_1)",
        },
        {
            "value": "chore_2",
            "label": "Feed the cat (Evening, 3 points, chore_2)",
        },
    ]
    assert chore_selector.config["multiple"] is True

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"chore_ids": ["chore_1", "chore_2"]},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_assignment_confirm"
    assert result["description_placeholders"] == {
        "name": "Isabelle",
        "titles": "Make the bed, Feed the cat",
        "count": "2",
    }

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "assignments_menu"
    assert loaded_config_entry.runtime_data.data["assignments"]["assignment_3"] == {
        "child_id": "kid_2",
        "chore_id": "chore_1",
        "active": True,
    }
    assert loaded_config_entry.runtime_data.data["assignments"]["assignment_4"] == {
        "child_id": "kid_2",
        "chore_id": "chore_2",
        "active": True,
    }

    entity_registry = er.async_get(hass)
    assert (
        entity_registry.async_get_entity_id(
            "switch",
            DOMAIN,
            "assignment_3",
        )
        == "switch.kid_2_chore_1"
    )

    result = await _select_menu_option(hass, result["flow_id"], "select_assignment")
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"assignment_id": "assignment_3"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "assignment_actions"
    assert result["description_placeholders"] == {
        "name": "Isabelle",
        "title": "Make the bed",
        "assignment_id": "assignment_3",
        "status": "Active",
        "availability": "Switch available",
    }
    assert result["menu_options"] == [
        "deactivate_assignment",
        "delete_assignment",
        "assignments_menu",
    ]

    result = await _select_menu_option(
        hass,
        result["flow_id"],
        "deactivate_assignment",
    )
    assert result["type"] is FlowResultType.MENU
    assert result["description_placeholders"]["status"] == "Inactive"
    assert (
        result["description_placeholders"]["availability"]
        == "Switch unavailable: assignment inactive"
    )

    result = await _select_menu_option(hass, result["flow_id"], "activate_assignment")
    assert result["type"] is FlowResultType.MENU
    assert result["description_placeholders"]["status"] == "Active"

    result = await _select_menu_option(hass, result["flow_id"], "delete_assignment")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "delete_assignment"

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "assignments_menu"
    assert "assignment_3" not in loaded_config_entry.runtime_data.data["assignments"]
    assert entity_registry.async_get_entity_id("switch", DOMAIN, "assignment_3") is None


async def test_options_flow_explains_when_no_assignment_pair_is_available(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test duplicate assignment pairs are filtered and explained."""
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
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

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_assignment_child")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "assignment_unavailable"
    assert result["errors"] == {"base": "no_available_assignment_pairs"}

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "assignments_menu"


async def test_options_flow_shows_assignment_parent_availability(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test assignment context distinguishes parent and assignment state."""
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
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
    await hass.services.async_call(
        DOMAIN,
        "set_child_active",
        {"child_id": "kid_1", "active": False},
        blocking=True,
    )

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(hass, result["flow_id"], "select_assignment")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"assignment_id": "assignment_1"},
    )

    assert result["type"] is FlowResultType.MENU
    assert result["description_placeholders"]["status"] == "Active"
    assert (
        result["description_placeholders"]["availability"]
        == "Switch unavailable: child inactive"
    )
