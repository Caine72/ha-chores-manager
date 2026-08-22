"""WebSocket API for Chores Manager."""

from datetime import date, timedelta
from typing import Any, cast

import voluptuous as vol

from homeassistant.auth.permissions.const import POLICY_CONTROL, POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import ATTR_AMOUNT, ATTR_ASSIGNMENT_ID, ATTR_CHILD_ID, ATTR_REASON, DOMAIN
from .exceptions import (
    CorrectionDateOutsideCurrentWeekError,
    UnknownAssignmentError,
    UnknownChildError,
)
from .models import ChoresManagerConfigEntry
from .storage import ChoresManagerStore

WS_TYPE_INVENTORY = f"{DOMAIN}/inventory"
WS_TYPE_CURRENT_WEEK_COMPLETIONS = f"{DOMAIN}/current_week_completions"
WS_TYPE_CURRENT_WEEK_HISTORY = f"{DOMAIN}/current_week_history"
WS_TYPE_SET_CURRENT_WEEK_COMPLETION = f"{DOMAIN}/set_current_week_completion"
WS_TYPE_WEEKLY_POINTS = f"{DOMAIN}/weekly_points"
WS_TYPE_ADJUST_WEEKLY_POINTS = f"{DOMAIN}/adjust_weekly_points"


def _nonzero_amount(value: int) -> int:
    """Validate that a signed adjustment amount is non-zero."""
    if value == 0:
        raise vol.Invalid("amount must not be zero")
    return value


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
    websocket_api.async_register_command(hass, websocket_current_week_history)
    websocket_api.async_register_command(hass, websocket_set_current_week_completion)
    websocket_api.async_register_command(hass, websocket_weekly_points)
    websocket_api.async_register_command(hass, websocket_adjust_weekly_points)


def _get_loaded_entry(hass: HomeAssistant) -> ChoresManagerConfigEntry | None:
    """Return the loaded Chores Manager config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)

    if len(entries) != 1 or entries[0].state is not ConfigEntryState.LOADED:
        return None

    return cast(ChoresManagerConfigEntry, entries[0])


def _get_points_entity_id(
    hass: HomeAssistant,
    store: ChoresManagerStore,
    child_id: str,
) -> str | None:
    """Resolve a child's weekly-points entity ID."""
    if child_id not in store.data["children"]:
        return None

    return er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN,
        DOMAIN,
        f"{child_id}_weekly_points",
    )


def _require_points_permission(
    connection: websocket_api.ActiveConnection,
    entity_id: str,
    permission: str,
) -> None:
    """Require an entity permission for a weekly-points command."""
    if not connection.user.permissions.check_entity(entity_id, permission):
        raise Unauthorized(
            user_id=connection.user.id,
            entity_id=entity_id,
            permission=permission,
        )


def _has_points_permission(
    connection: websocket_api.ActiveConnection,
    entity_id: str,
    permission: str,
) -> bool:
    """Return whether a connection has an entity permission."""
    return connection.user.permissions.check_entity(entity_id, permission)


def _build_weekly_points(
    hass: HomeAssistant,
    store: ChoresManagerStore,
    child_id: str,
) -> dict[str, Any] | None:
    """Build current and previous weekly totals for one child."""
    points_entity_id = _get_points_entity_id(hass, store, child_id)
    if points_entity_id is None:
        return None

    current_start, current_end = store.get_current_week_bounds()
    previous_start = current_start - timedelta(days=7)
    previous_end = current_start - timedelta(days=1)

    result = {
        "child_id": child_id,
        "child_name": store.data["children"][child_id]["name"],
        "points_entity_id": points_entity_id,
        "current_week": {
            "start": current_start.isoformat(),
            "end": current_end.isoformat(),
            "points": store.get_week_points(child_id, current_start),
        },
        "previous_week": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            "points": store.get_week_points(child_id, previous_start),
        },
    }
    if person_entity_id := store.data["children"][child_id].get("person_entity_id"):
        result["person_entity_id"] = person_entity_id
    return result


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
                **(
                    {"person_entity_id": child["person_entity_id"]}
                    if child.get("person_entity_id")
                    else {}
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
    child_id: str | None = None,
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
            for completion_id, completion in store.get_current_week_completions(
                child_id
            )
        ],
    }


def _build_current_week_history(
    store: ChoresManagerStore,
    child_id: str,
    points_entity_id: str,
) -> dict[str, Any]:
    """Build entity-authorized current-week history for one child."""
    history = _build_current_week_completions(store, child_id)
    result = {
        "child_id": child_id,
        "child_name": store.data["children"][child_id]["name"],
        "points_entity_id": points_entity_id,
        **history,
    }
    if person_entity_id := store.data["children"][child_id].get("person_entity_id"):
        result["person_entity_id"] = person_entity_id
    return result


@callback
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_WEEKLY_POINTS,
        vol.Required(ATTR_CHILD_ID): vol.All(str, str.strip, vol.Length(min=1)),
    }
)
def websocket_weekly_points(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return authorized current and previous weekly points for a child."""
    entry = _get_loaded_entry(hass)
    if entry is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "Chores Manager is not loaded",
        )
        return

    result = _build_weekly_points(hass, entry.runtime_data, msg[ATTR_CHILD_ID])
    if result is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"Child {msg[ATTR_CHILD_ID]} or its weekly-points entity does not exist",
        )
        return

    _require_points_permission(connection, result["points_entity_id"], POLICY_READ)
    result["can_adjust"] = _has_points_permission(
        connection,
        result["points_entity_id"],
        POLICY_CONTROL,
    )
    connection.send_result(msg["id"], result)


@callback
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_CURRENT_WEEK_HISTORY,
        vol.Required(ATTR_CHILD_ID): vol.All(str, str.strip, vol.Length(min=1)),
    }
)
def websocket_current_week_history(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return authorized current-week completion history for one child."""
    entry = _get_loaded_entry(hass)
    if entry is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "Chores Manager is not loaded",
        )
        return

    child_id = msg[ATTR_CHILD_ID]
    points_entity_id = _get_points_entity_id(hass, entry.runtime_data, child_id)
    if points_entity_id is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"Child {child_id} or its weekly-points entity does not exist",
        )
        return

    _require_points_permission(connection, points_entity_id, POLICY_READ)
    result = _build_current_week_history(
        entry.runtime_data,
        child_id,
        points_entity_id,
    )
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_ADJUST_WEEKLY_POINTS,
        vol.Required(ATTR_CHILD_ID): vol.All(str, str.strip, vol.Length(min=1)),
        vol.Required(ATTR_AMOUNT): vol.All(
            vol.Coerce(int),
            vol.Range(min=-100, max=100),
            _nonzero_amount,
        ),
        vol.Optional(ATTR_REASON): vol.All(
            str,
            str.strip,
            vol.Length(min=1, max=200),
        ),
    }
)
@websocket_api.async_response
async def websocket_adjust_weekly_points(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Make an authorized audited adjustment to current weekly points."""
    entry = _get_loaded_entry(hass)
    if entry is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            "Chores Manager is not loaded",
        )
        return

    store = entry.runtime_data
    entity_id = _get_points_entity_id(hass, store, msg[ATTR_CHILD_ID])
    if entity_id is None:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"Child {msg[ATTR_CHILD_ID]} or its weekly-points entity does not exist",
        )
        return

    _require_points_permission(connection, entity_id, POLICY_CONTROL)
    previous_total = store.get_current_week_points(msg[ATTR_CHILD_ID])

    try:
        adjustment_id = await store.async_adjust_weekly_counter(
            msg[ATTR_CHILD_ID],
            msg[ATTR_AMOUNT],
            msg.get(ATTR_REASON),
        )
    except UnknownChildError:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_NOT_FOUND,
            f"Child {msg[ATTR_CHILD_ID]} does not exist",
        )
        return

    current_total = store.get_current_week_points(msg[ATTR_CHILD_ID])
    connection.send_result(
        msg["id"],
        {
            "child_id": msg[ATTR_CHILD_ID],
            "points_entity_id": entity_id,
            "adjustment_id": adjustment_id,
            "requested_amount": msg[ATTR_AMOUNT],
            "applied_amount": current_total - previous_total,
            "current_points": current_total,
        },
    )


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
