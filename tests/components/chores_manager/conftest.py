"""Fixtures for Chores Manager tests."""

from pathlib import Path

import pytest

from homeassistant.core import HomeAssistant

from .common import DOMAIN, NAME

from tests.common import MockConfigEntry


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> None:
    """Enable loading custom integrations in every test."""


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Expose Chores Manager in the temporary Home Assistant config."""
    config_dir = Path(hass_tmp_config_dir)
    custom_components_dir = config_dir / "custom_components"
    custom_components_dir.mkdir(exist_ok=True)
    (custom_components_dir / "__init__.py").touch()

    integration_dir = Path(__file__).resolve().parents[3] / "custom_components" / DOMAIN
    (custom_components_dir / DOMAIN).symlink_to(
        integration_dir,
        target_is_directory=True,
    )

    return hass_tmp_config_dir


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create the singleton Chores Manager config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def loaded_config_entry(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up and return the Chores Manager config entry."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
