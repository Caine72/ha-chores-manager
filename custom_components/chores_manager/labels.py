"""Label management for Chores Manager."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, label_registry as lr

from .const import CHORES_LABEL_DESCRIPTION, CHORES_LABEL_ICON, CHORES_LABEL_NAME
from .storage import ChoresManagerStore

_LOGGER = logging.getLogger(__name__)


async def async_initialize_assignment_label(
    hass: HomeAssistant,
    store: ChoresManagerStore,
    assignment_id: str,
    registry_entry: er.RegistryEntry | None,
) -> None:
    """Apply the default chore label to an assignment entity once."""
    if store.is_assignment_label_initialized(assignment_id):
        return

    if registry_entry is None:
        _LOGGER.warning(
            "Cannot initialize the Chores label for %s because the "
            "entity has no registry entry",
            assignment_id,
        )
        return

    label_registry = lr.async_get(hass)
    label = label_registry.async_get_label_by_name(CHORES_LABEL_NAME)

    if label is None:
        label = label_registry.async_create(
            CHORES_LABEL_NAME,
            icon=CHORES_LABEL_ICON,
            description=CHORES_LABEL_DESCRIPTION,
        )

    entity_registry = er.async_get(hass)
    current_entry = entity_registry.async_get(registry_entry.entity_id)

    if current_entry is None:
        _LOGGER.warning(
            "Cannot initialize the Chores label because registry entry "
            "%s no longer exists",
            registry_entry.entity_id,
        )
        return

    if label.label_id not in current_entry.labels:
        current_entry = entity_registry.async_update_entity(
            current_entry.entity_id,
            labels={
                *current_entry.labels,
                label.label_id,
            },
        )

    if label.label_id not in current_entry.labels:
        _LOGGER.error(
            "Failed to apply label %s to %s",
            label.label_id,
            current_entry.entity_id,
        )
        return

    await store.async_mark_assignment_label_initialized(assignment_id)
