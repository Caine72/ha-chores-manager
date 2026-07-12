"""Test the Chores Manager WebSocket API."""

from datetime import timedelta
from typing import Any

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .common import DOMAIN

from tests.common import MockConfigEntry
from tests.typing import WebSocketGenerator

CHORE_SWITCH = "switch.kid_1_chore_1"
POINTS_SENSOR = "sensor.kid_1_weekly_points"
WS_TYPE_INVENTORY = "chores_manager/inventory"
WS_TYPE_CURRENT_WEEK_COMPLETIONS = "chores_manager/current_week_completions"


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


async def _get_inventory(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> dict[str, Any]:
    """Fetch Chores Manager inventory over WebSocket."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": WS_TYPE_INVENTORY})
    return await client.receive_json()


async def _get_current_week_completions(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> dict[str, Any]:
    """Fetch current-week correction history over WebSocket."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": WS_TYPE_CURRENT_WEEK_COMPLETIONS})
    return await client.receive_json()


async def test_inventory_returns_stored_structure_and_entity_registry_ids(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test inventory exposes structure, inactive records, and registry IDs."""
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
            "sort_order": 5,
        },
    )

    entity_registry = er.async_get(hass)
    entity_registry.async_update_entity(
        POINTS_SENSOR,
        new_entity_id="sensor.alex_weekly_points",
    )
    entity_registry.async_update_entity(
        CHORE_SWITCH,
        new_entity_id="switch.alex_make_the_bed",
    )

    await _call_action(
        hass,
        "set_assignment_active",
        {"assignment_id": "assignment_1", "active": False},
    )
    await _call_action(
        hass,
        "set_child_active",
        {"child_id": "kid_2", "active": False},
    )
    await _call_action(
        hass,
        "set_chore_active",
        {"chore_id": "chore_1", "active": False},
    )

    week_start, week_end = loaded_config_entry.runtime_data.get_current_week_bounds()

    response = await _get_inventory(hass, hass_ws_client)

    assert response["success"]
    assert response["result"] == {
        "children": [
            {
                "child_id": "kid_1",
                "name": "Alex",
                "active": True,
                "points_entity_id": "sensor.alex_weekly_points",
            },
            {
                "child_id": "kid_2",
                "name": "Isabelle",
                "active": False,
                "points_entity_id": "sensor.kid_2_weekly_points",
            },
        ],
        "chores": [
            {
                "chore_id": "chore_1",
                "title": "Make the bed",
                "category": "Morning",
                "points": 2,
                "icon": "mdi:bed",
                "active": False,
                "sort_order": 5,
                "completion_mode": "independent",
            }
        ],
        "assignments": [
            {
                "assignment_id": "assignment_1",
                "child_id": "kid_1",
                "chore_id": "chore_1",
                "active": False,
                "switch_expected": False,
                "switch_entity_id": "switch.alex_make_the_bed",
            },
            {
                "assignment_id": "assignment_2",
                "child_id": "kid_2",
                "chore_id": "chore_1",
                "active": True,
                "switch_expected": False,
                "switch_entity_id": "switch.kid_2_chore_1",
            },
        ],
        "week": {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
    }


@pytest.mark.usefixtures("loaded_config_entry")
async def test_inventory_does_not_expose_completion_history(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test inventory omits completion records."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
        },
    )
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": CHORE_SWITCH},
        blocking=True,
    )
    await hass.async_block_till_done()

    response = await _get_inventory(hass, hass_ws_client)

    assert response["success"]
    assert set(response["result"]) == {"children", "chores", "assignments", "week"}


async def test_current_week_completions_returns_current_window_and_orphans(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test correction history exposes current-week snapshots and orphan state."""
    await _call_action(hass, "add_child", {"name": "Alex"})
    await _call_action(
        hass,
        "add_chore",
        {
            "title": "Make the bed",
            "category": "Morning",
            "points": 2,
        },
    )
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": CHORE_SWITCH},
        blocking=True,
    )
    await hass.async_block_till_done()

    store = loaded_config_entry.runtime_data
    week_start, _ = store.get_current_week_bounds()
    store.data["completions"]["completion_2"] = {
        "completed_at": dt_util.utcnow().isoformat(),
        "local_date": (week_start - timedelta(days=1)).isoformat(),
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "assignment_id": "assignment_1",
        "child_name": "Alex",
        "chore_title": "Make the bed",
        "category": "Morning",
        "points": 2,
    }
    store.data["next_completion_id"] = 3
    await store.async_save()

    await _call_action(
        hass,
        "delete_assignment",
        {"assignment_id": "assignment_1"},
    )

    response = await _get_current_week_completions(hass, hass_ws_client)

    assert response["success"]
    assert response["result"] == {
        "window": {
            "start": week_start.isoformat(),
            "end": dt_util.now().date().isoformat(),
        },
        "completions": [
            {
                "completion_id": "completion_1",
                "assignment_id": "assignment_1",
                "assignment_exists": False,
                "child_id": "kid_1",
                "chore_id": "chore_1",
                "local_date": dt_util.now().date().isoformat(),
                "completed_at": store.data["completions"]["completion_1"][
                    "completed_at"
                ],
                "child_name": "Alex",
                "chore_title": "Make the bed",
                "category": "Morning",
                "points": 2,
            }
        ],
    }


async def test_inventory_requires_loaded_entry(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test inventory fails when Chores Manager is not loaded."""
    assert await hass.config_entries.async_unload(loaded_config_entry.entry_id)
    await hass.async_block_till_done()

    response = await _get_inventory(hass, hass_ws_client)

    assert not response["success"]
    assert response["error"]["code"] == "not_found"
    assert response["error"]["message"] == "Chores Manager is not loaded"


@pytest.mark.usefixtures("loaded_config_entry")
async def test_inventory_requires_admin(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
) -> None:
    """Test inventory rejects non-admin users."""
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id({"type": WS_TYPE_INVENTORY})
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "unauthorized"


@pytest.mark.usefixtures("loaded_config_entry")
async def test_current_week_completions_requires_admin(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
) -> None:
    """Test correction history rejects non-admin users."""
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id({"type": WS_TYPE_CURRENT_WEEK_COMPLETIONS})
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "unauthorized"
