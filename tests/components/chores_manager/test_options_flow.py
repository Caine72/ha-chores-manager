"""Test Chores Manager native management options flow."""

from datetime import date
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .common import DOMAIN

from tests.common import MockConfigEntry, MockUser


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


async def test_options_flow_changes_week_boundary_immediately(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test reset-after Thursday immediately selects the Thursday just passed."""
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    assert result["menu_options"] == [
        "week_settings",
        "children_menu",
        "chores_menu",
        "assignments_menu",
    ]

    result = await _select_menu_option(hass, result["flow_id"], "week_settings")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "week_settings"
    weekday_key = next(
        key
        for key in result["data_schema"].schema
        if key.schema == "reset_after_weekday"
    )
    assert weekday_key.default() == "friday"
    weekday_selector = result["data_schema"].schema[weekday_key]
    assert weekday_selector.config["options"] == [
        {"value": "monday", "label": "Monday"},
        {"value": "tuesday", "label": "Tuesday"},
        {"value": "wednesday", "label": "Wednesday"},
        {"value": "thursday", "label": "Thursday"},
        {"value": "friday", "label": "Friday"},
        {"value": "saturday", "label": "Saturday"},
        {"value": "sunday", "label": "Sunday"},
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"reset_after_weekday": "thursday"},
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"
    assert loaded_config_entry.options["reset_after_weekday"] == "thursday"
    assert loaded_config_entry.runtime_data.reset_after_weekday == "thursday"
    assert loaded_config_entry.runtime_data.get_current_week_bounds(
        date(2026, 8, 22)
    ) == (date(2026, 8, 21), date(2026, 8, 27))


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
    person_key = next(
        key for key in result["data_schema"].schema if key.schema == "person_entity_id"
    )
    assert result["data_schema"].schema[person_key].config["domain"] == ["person"]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Alex", "person_entity_id": "person.alex"},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "children_menu"
    assert loaded_config_entry.runtime_data.data["children"]["kid_1"] == {
        "name": "Alex",
        "active": True,
        "person_entity_id": "person.alex",
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
    person_key = next(
        key for key in result["data_schema"].schema if key.schema == "person_entity_id"
    )
    assert person_key.description == {"suggested_value": "person.alex"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Alexandra"},
    )
    assert result["type"] is FlowResultType.MENU
    assert (
        loaded_config_entry.runtime_data.data["children"]["kid_1"]["name"]
        == "Alexandra"
    )
    assert (
        "person_entity_id"
        not in loaded_config_entry.runtime_data.data["children"]["kid_1"]
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


async def test_options_flow_manages_child_adjustment_users(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
    hass_read_only_user: MockUser,
) -> None:
    """Test child management configures and clears the adjustment allowlist."""
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_child")

    user_ids_key = next(
        key
        for key in result["data_schema"].schema
        if key.schema == "adjustment_user_ids"
    )
    user_selector = result["data_schema"].schema[user_ids_key]
    assert user_selector.config["multiple"] is True
    assert hass_read_only_user.id in {
        option["value"] for option in user_selector.config["options"]
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "name": "Alex",
            "restrict_adjustments": True,
            "adjustment_user_ids": [hass_read_only_user.id],
        },
    )
    child = loaded_config_entry.runtime_data.data["children"]["kid_1"]
    assert child["adjustment_user_ids"] == [hass_read_only_user.id]

    result = await _select_menu_option(hass, result["flow_id"], "select_child")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"child_id": "kid_1"},
    )
    result = await _select_menu_option(hass, result["flow_id"], "edit_child")
    restrict_key = next(
        key
        for key in result["data_schema"].schema
        if key.schema == "restrict_adjustments"
    )
    assert restrict_key.description == {"suggested_value": True}
    user_ids_key = next(
        key
        for key in result["data_schema"].schema
        if key.schema == "adjustment_user_ids"
    )
    assert user_ids_key.description == {"suggested_value": [hass_read_only_user.id]}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Alex", "restrict_adjustments": False},
    )
    assert result["step_id"] == "child_actions"
    assert (
        "adjustment_user_ids"
        not in loaded_config_entry.runtime_data.data["children"]["kid_1"]
    )


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


async def test_options_flow_removes_multiple_chore_assignments(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test removing multiple active and inactive chore assignments."""
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
        "set_chore_active",
        {"chore_id": "chore_2", "active": False},
        blocking=True,
    )

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    assert "remove_assignment_child" in result["menu_options"]

    result = await _select_menu_option(
        hass,
        result["flow_id"],
        "remove_assignment_child",
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_assignment_child"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"child_id": "kid_1"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_assignment_chore"
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
            "label": "Feed the cat (Evening, 3 points, chore_2, inactive)",
        },
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"chore_ids": ["chore_1", "chore_2"]},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "remove_assignment_confirm"
    assert result["description_placeholders"] == {
        "name": "Alex",
        "titles": "Make the bed, Feed the cat",
        "count": "2",
    }

    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "assignments_menu"
    assert loaded_config_entry.runtime_data.data["assignments"] == {}

    entity_registry = er.async_get(hass)
    assert entity_registry.async_get_entity_id("switch", DOMAIN, "assignment_1") is None
    assert entity_registry.async_get_entity_id("switch", DOMAIN, "assignment_2") is None


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


async def test_options_flow_empty_and_inactive_household_guidance(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test empty and inactive households return useful management guidance."""
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    assert result["menu_options"] == ["add_child", "init"]

    result = await _select_menu_option(hass, result["flow_id"], "init")
    result = await _select_menu_option(hass, result["flow_id"], "chores_menu")
    assert result["menu_options"] == ["add_chore", "init"]

    result = await _select_menu_option(hass, result["flow_id"], "init")
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_assignment_child")
    assert result["step_id"] == "assignment_unavailable"
    assert result["errors"] == {"base": "no_active_assignment_children"}

    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    result = await _select_menu_option(hass, result["flow_id"], "add_assignment_child")
    assert result["step_id"] == "assignment_unavailable"
    assert result["errors"] == {"base": "no_active_assignment_chores"}


async def test_options_flow_rejects_stale_and_tampered_selections(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test selectors recover when household data changes while a flow is open."""
    for name in ("Alex", "Isabelle", "Jordan"):
        await hass.services.async_call(
            DOMAIN,
            "add_child",
            {"name": name},
            blocking=True,
        )
    await hass.services.async_call(
        DOMAIN,
        "add_chore",
        {"title": "Make the bed", "category": "Morning", "points": 2},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "add_chore",
        {"title": "Feed the cat", "category": "Evening", "points": 3},
        blocking=True,
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    result = await _select_menu_option(hass, result["flow_id"], "select_child")
    await hass.services.async_call(
        DOMAIN, "delete_child", {"child_id": "kid_3"}, blocking=True
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"child_id": "kid_3"}
    )
    assert result["step_id"] == "select_child"
    assert result["errors"] == {"base": "unknown_child"}

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "chores_menu")
    result = await _select_menu_option(hass, result["flow_id"], "select_chore")
    await hass.services.async_call(
        DOMAIN, "delete_chore", {"chore_id": "chore_1"}, blocking=True
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"chore_id": "chore_1"}
    )
    assert result["step_id"] == "select_chore"
    assert result["errors"] == {"base": "unknown_chore"}

    await hass.services.async_call(
        DOMAIN,
        "add_chore",
        {"title": "Feed the cat", "category": "Evening", "points": 3},
        blocking=True,
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(hass, result["flow_id"], "select_assignment")
    await hass.services.async_call(
        DOMAIN,
        "delete_assignment",
        {"assignment_id": "assignment_4"},
        blocking=True,
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"assignment_id": "assignment_4"}
    )
    assert result["step_id"] == "select_assignment"
    assert result["errors"] == {"base": "unknown_assignment"}

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(
        hass, result["flow_id"], "remove_assignment_child"
    )
    await hass.services.async_call(
        DOMAIN, "delete_child", {"child_id": "kid_2"}, blocking=True
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"child_id": "kid_2"}
    )
    assert result["step_id"] == "remove_assignment_child"
    assert result["errors"] == {"base": "unknown_child"}

    await hass.services.async_call(
        DOMAIN, "add_child", {"name": "Casey"}, blocking=True
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "assignments_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_assignment_child")
    await hass.services.async_call(
        DOMAIN, "delete_child", {"child_id": "kid_4"}, blocking=True
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"child_id": "kid_4"}
    )
    assert result["step_id"] == "add_assignment_child"
    assert result["errors"] == {"base": "unknown_child"}


async def test_options_flow_surfaces_action_failures_and_allows_retry(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test a transient action failure keeps the form open for a safe retry."""
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    result = await _select_menu_option(hass, result["flow_id"], "add_child")

    error = ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="unknown_child",
    )
    with patch(
        "homeassistant.core.ServiceRegistry.async_call",
        AsyncMock(side_effect=error),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"name": "Alex"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_child"
    assert result["errors"] == {"base": "unknown_child"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "Alex"}
    )
    assert result["type"] is FlowResultType.MENU
    assert loaded_config_entry.runtime_data.data["children"]["kid_1"]["name"] == "Alex"


async def test_options_flow_recovers_from_objects_removed_mid_flow(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test management returns to a safe menu when selected data disappears."""
    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "add_chore",
        {"title": "Make the bed", "category": "Morning", "points": 2},
        blocking=True,
    )

    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "children_menu")
    result = await _select_menu_option(hass, result["flow_id"], "select_child")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"child_id": "kid_1"}
    )
    await hass.services.async_call(
        DOMAIN,
        "delete_child",
        {"child_id": "kid_1"},
        blocking=True,
    )
    result = await _select_menu_option(hass, result["flow_id"], "edit_child")
    assert result["step_id"] == "children_menu"

    await hass.services.async_call(
        DOMAIN,
        "add_child",
        {"name": "Alex"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "add_assignment",
        {"child_id": "kid_2", "chore_id": "chore_1"},
        blocking=True,
    )
    result = await hass.config_entries.options.async_init(loaded_config_entry.entry_id)
    result = await _select_menu_option(hass, result["flow_id"], "chores_menu")
    result = await _select_menu_option(hass, result["flow_id"], "select_chore")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"chore_id": "chore_1"}
    )
    await hass.services.async_call(
        DOMAIN,
        "delete_chore",
        {"chore_id": "chore_1"},
        blocking=True,
    )
    result = await _select_menu_option(hass, result["flow_id"], "edit_chore")
    assert result["step_id"] == "chores_menu"
