"""Test Chores Manager setup and unloading."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .common import DOMAIN

from tests.common import MockConfigEntry


async def test_setup_and_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Test that the singleton config entry sets up and unloads cleanly."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.runtime_data is not None

    assert hass.services.has_service(DOMAIN, "add_assignment")
    assert hass.services.has_service(DOMAIN, "add_child")
    assert hass.services.has_service(DOMAIN, "add_chore")
    assert hass.services.has_service(DOMAIN, "set_assignment_active")
    assert hass.services.has_service(DOMAIN, "set_child_active")
    assert hass.services.has_service(DOMAIN, "set_chore_active")
    assert hass.services.has_service(DOMAIN, "update_child")
    assert hass.services.has_service(DOMAIN, "update_chore")

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED
