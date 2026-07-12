"""WebSocket API for Chores Manager."""

from datetime import date
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import ATTR_ASSIGNMENT_ID, DOMAIN
from .exceptions import CorrectionDateOutsideCurrentWeekError, UnknownAssignmentError
from .models import ChoresManagerConfigEntry
from .storage import ChoresManagerStore

WS_TYPE_INVENTORY = f"{DOMAIN}/inventory"
WS_TYPE_CURRENT_WEEK_COMPLETIONS = f"{DOMAIN}/current_week_completions"
WS_TYPE_SET_CURRENT_WEEK_COMPLETION = f"{DOMAIN}/set_current_week_completion"


def _stable_id_sort_key(stable_id: str) -> tuple[str, int, str]:
    """Return a deterministic sort key for integration stable IDs."""
    prefix, _, suffix = stable_id.rpartition("_")

    if suffix.isdecimal():
        return (prefix, int(suffix), "")

    return (prefix, -1, suffix)


@callback
def async_setup(hass: HomeAssistant) -> None:
    """Set up the Chores Manager WebSocket API."""
    websocket_api.async_register_command(hass, websocket_inventory)
    websocket_api.async_register_command(hass, websocket_current_week_completions)
    websocket_api.async_register_command(hass, websocket_set_current_week_completion)


def _get_loaded_entry(hass: HomeAssistant) -> ChoresManagerConfigEntry | None:
    """Return the loaded Chores Manager config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)

    if len(entries) != 1 or entries[0].state is not ConfigEntryState.LOADED:
        return None

    return cast(ChoresManagerConfigEntry, entries[0])


def _build_inventory(
    hass: HomeAssistant,
    store: ChoresManagerStore,
) -> dict[str, Any]:
    """Build the read-only inventory response."""
    entity_registry = er.async_get(hass)
    week_start, week_end = store.get_current_week_bounds()

    return {
        "children": [
            {
                "child_id": child_id,
                "name": child["name"],
                "active": child["active"],
                "points_entity_id": entity_registry.async_get_entity_id(
                    SENSOR_DOMAIN,
                    DOMAIN,
                    f"{child_id}_weekly_points",
                ),
            }
            for child_id, child in sorted(
                store.data["children"].items(),
                key=lambda item: _stable_id_sort_key(item[0]),
            )
        ],
        "chores": [
            {
                "chore_id": chore_id,
                "title": chore["title"],
                "category": chore["category"],
                "points": chore["points"],
                "icon": chore["icon"],
                "active": chore["active"],
                "sort_order": chore["sort_order"],
                "completion_mode": chore["completion_mode"],
            }
            for chore_id, chore in sorted(
                store.data["chores"].items(),
                key=lambda item: _stable_id_sort_key(item[0]),
            )
        ],
        "assignments": [
            {
                "assignment_id": assignment_id,
                "child_id": assignment["child_id"],
                "chore_id": assignment["chore_id"],
                "active": assignment["active"],
                "switch_expected": assignment["active"]
                and store.data["children"][assignment["child_id"]]["active"]
                and store.data["chores"][assignment["chore_id"]]["active"],
                "switch_entity_id": entity_registry.async_get_entity_id(
                    SWITCH_DOMAIN,
                    DOMAIN,
                    assignment_id,
                ),
            }
            for assignment_id, assignment in sorted(
                store.data["assignments"].items(),
                key=lambda item: _stable_id_sort_key(item[0]),
            )
        ],
        "week": {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
    }


def _build_current_week_completions(
    store: ChoresManagerStore,
) -> dict[str, Any]:
    """Build the read-only current-week correction history response."""
    week_start, _ = store.get_current_week_bounds()
    today = dt_util.now().date()

    return {
        "window": {
            "start": week_start.isoformat(),
            "end": today.isoformat(),
        },
        "completions": [
            {
                "completion_id": completion_id,
                "assignment_id": completion["assignment_id"],
                "assignment_exists": completion["assignment_id"]
                in store.data["assignments"],
                "child_id": completion["child_id"],
                "chore_id": completion["chore_id"],
                "local_date": completion["local_date"],
                "completed_at": completion["completed_at"],
                "child_name": completion["child_name"],
                "chore_title": completion["chore_title"],
                "category": completion["category"],
                "points": completion["points"],
            }
            for completion_id, completion in store.get_current_week_completions()
        ],
    }


@callback
@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_INVENTORY})
def websocket_inventory(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the read-only Chores Manager inventory."""
    entry = _get_loaded_entry(hass)

    if entry is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "Chores Manager is not loaded",
        )
        return

    connection.send_result(msg["id"], _build_inventory(hass, entry.runtime_data))


@callback
@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): WS_TYPE_CURRENT_WEEK_COMPLETIONS}
)
def websocket_current_week_completions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return correction history for the current chore week through today."""
    entry = _get_loaded_entry(hass)

    if entry is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "Chores Manager is not loaded",
        )
        return

    connection.send_result(
        msg["id"],
        _build_current_week_completions(entry.runtime_data),
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_SET_CURRENT_WEEK_COMPLETION,
        vol.Required(ATTR_ASSIGNMENT_ID): vol.All(str, str.strip, vol.Length(min=1)),
        vol.Required("local_date"): vol.All(str, str.strip, vol.Length(min=1)),
        vol.Required("completed"): bool,
    }
)
@websocket_api.async_response
async def websocket_set_current_week_completion(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Correct an assignment completion within the current chore week."""
    entry = _get_loaded_entry(hass)

    if entry is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "Chores Manager is not loaded",
        )
        return

    try:
        local_date = date.fromisoformat(msg["local_date"])
    except ValueError:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_INVALID_FORMAT,
            "local_date must use YYYY-MM-DD format",
        )
        return

    try:
        (
            completion_id,
            changed,
        ) = await entry.runtime_data.async_set_current_week_completion(
            msg[ATTR_ASSIGNMENT_ID],
            local_date,
            msg["completed"],
        )
    except CorrectionDateOutsideCurrentWeekError:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_INVALID_FORMAT,
            "local_date must be within the current chore week through today",
        )
        return
    except UnknownAssignmentError as err:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"Assignment {err.assignment_id} does not exist",
        )
        return

    connection.send_result(
        msg["id"],
        {
            "assignment_id": msg[ATTR_ASSIGNMENT_ID],
            "local_date": local_date.isoformat(),
            "completed": msg["completed"],
            "completion_id": completion_id,
            "changed": changed,
        },
    )
