"""The Chores Manager integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import PLATFORMS
from .models import ChoresManagerConfigEntry
from .services import async_setup_services
from .storage import ChoresManagerStore


async def async_setup(
    hass: HomeAssistant,
    config: ConfigType,
) -> bool:
    """Set up the Chores Manager integration."""
    await async_setup_services(hass, config)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChoresManagerConfigEntry,
) -> bool:
    """Set up Chores Manager from a config entry."""
    manager_store = ChoresManagerStore(hass)
    await manager_store.async_load()

    entry.runtime_data = manager_store

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ChoresManagerConfigEntry,
) -> bool:
    """Unload a Chores Manager config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
