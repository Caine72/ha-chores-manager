"""Test Chores Manager native management options flow."""

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "chores_menu")
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "chores_menu"

    result = await _select_menu_option(hass, result["flow_id"], "add_chore")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_chore"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
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
    """Test the options flow reports the existing no-active-children error."""
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
    assert result["errors"] == {"base": "no_active_children"}
