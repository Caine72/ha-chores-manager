"""Test Chores Manager date-bound state and completion retention."""

from freezegun import freeze_time
import pytest

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from .common import DOMAIN

from tests.common import MockConfigEntry

CHORE_SWITCH = "switch.kid_1_chore_1"
WEEKLY_POINTS_SENSOR = "sensor.kid_1_weekly_points"


@pytest.fixture(autouse=True)
async def use_utc_time_zone(hass: HomeAssistant) -> None:
    """Use UTC so frozen timestamps map directly to local dates."""
    await hass.config.async_set_time_zone("UTC")


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
) -> None:
    """Call a switch action and wait for Chores Manager updates."""
    await hass.services.async_call(
        "switch",
        action,
        {ATTR_ENTITY_ID: CHORE_SWITCH},
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


def _completion(local_date: str) -> dict[str, str | int]:
    """Create a stored completion snapshot for an assignment."""
    return {
        "completed_at": f"{local_date}T08:00:00+00:00",
        "local_date": local_date,
        "child_id": "kid_1",
        "chore_id": "chore_1",
        "assignment_id": "assignment_1",
        "child_name": "Alex",
        "chore_title": "Make the bed",
        "category": "Morning",
        "points": 2,
    }


async def test_regular_midnight_refreshes_daily_state_without_resetting_points(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test a normal midnight clears today's state but keeps weekly points."""
    with freeze_time("2026-07-06 23:59:00+00:00"):
        await _create_assignment(hass)
        await _call_switch_action(hass, "turn_on")

        assert _state(hass, CHORE_SWITCH).state == "on"
        assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"

    with freeze_time("2026-07-07 00:00:00+00:00"):
        store = loaded_config_entry.runtime_data
        await store.async_handle_local_midnight(dt_util.now())
        await hass.async_block_till_done()

        assert _state(hass, CHORE_SWITCH).state == "off"
        points_state = _state(hass, WEEKLY_POINTS_SENSOR)
        assert points_state.state == "2"
        assert points_state.attributes["week_start"] == "2026-07-04"
        assert points_state.attributes["week_end"] == "2026-07-10"
        assert list(store.data["completions"]) == ["completion_1"]


async def test_saturday_rollover_starts_new_week_and_retains_previous_completion(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test Friday-to-Saturday rollover resets current-week entity state."""
    with freeze_time("2026-07-10 23:59:00+00:00"):
        await _create_assignment(hass)
        await _call_switch_action(hass, "turn_on")

        assert _state(hass, CHORE_SWITCH).state == "on"
        assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"

    with freeze_time("2026-07-11 00:00:00+00:00"):
        store = loaded_config_entry.runtime_data
        await store.async_handle_local_midnight(dt_util.now())
        await hass.async_block_till_done()

        assert _state(hass, CHORE_SWITCH).state == "off"
        points_state = _state(hass, WEEKLY_POINTS_SENSOR)
        assert points_state.state == "0"
        assert points_state.attributes["week_start"] == "2026-07-11"
        assert points_state.attributes["week_end"] == "2026-07-17"
        assert store.data["completions"]["completion_1"]["local_date"] == ("2026-07-10")


async def test_saturday_pruning_keeps_current_and_previous_chore_weeks(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test Saturday pruning retains exactly the current and previous weeks."""
    with freeze_time("2026-07-18 00:00:00+00:00"):
        await _create_assignment(hass)

        store = loaded_config_entry.runtime_data
        store.data["completions"] = {
            "completion_1": _completion("2026-07-10"),
            "completion_2": _completion("2026-07-11"),
            "completion_3": _completion("2026-07-17"),
            "completion_4": _completion("2026-07-18"),
        }
        store.data["next_completion_id"] = 5
        await store.async_save()
        await hass.async_block_till_done()

        await store.async_handle_local_midnight(dt_util.now())
        await hass.async_block_till_done()

        assert list(store.data["completions"]) == [
            "completion_2",
            "completion_3",
            "completion_4",
        ]
        assert store.data["next_completion_id"] == 5
        assert _state(hass, CHORE_SWITCH).state == "on"
        assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"


async def test_loading_store_prunes_completions_outside_retention(
    hass: HomeAssistant,
    loaded_config_entry: MockConfigEntry,
) -> None:
    """Test setup also applies the two-week completion retention policy."""
    with freeze_time("2026-07-18 08:00:00+00:00"):
        await _create_assignment(hass)

        store = loaded_config_entry.runtime_data
        store.data["completions"] = {
            "completion_1": _completion("2026-07-10"),
            "completion_2": _completion("2026-07-11"),
            "completion_3": _completion("2026-07-18"),
        }
        store.data["next_completion_id"] = 4
        await store.async_save()
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(loaded_config_entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_setup(loaded_config_entry.entry_id)
        await hass.async_block_till_done()

        reloaded_store = loaded_config_entry.runtime_data
        assert list(reloaded_store.data["completions"]) == [
            "completion_2",
            "completion_3",
        ]
        assert reloaded_store.data["next_completion_id"] == 4
        assert _state(hass, CHORE_SWITCH).state == "on"
        assert _state(hass, WEEKLY_POINTS_SENSOR).state == "2"
