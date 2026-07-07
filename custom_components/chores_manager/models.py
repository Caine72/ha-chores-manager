"""Data models for Chores Manager."""

from homeassistant.config_entries import ConfigEntry

from .storage import ChoresManagerStore

type ChoresManagerConfigEntry = ConfigEntry[ChoresManagerStore]
