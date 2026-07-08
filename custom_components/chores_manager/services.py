"""Actions provided by Chores Manager."""

from typing import cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_ACTIVE,
    ATTR_CATEGORY,
    ATTR_CHILD_ID,
    ATTR_CHILD_IDS,
    ATTR_CHORE_ID,
    ATTR_ICON,
    ATTR_NAME,
    ATTR_POINTS,
    ATTR_SORT_ORDER,
    ATTR_TITLE,
    DEFAULT_CHORE_ICON,
    DOMAIN,
    SERVICE_ADD_CHILD,
    SERVICE_ADD_CHORE,
    SERVICE_SET_CHILD_ACTIVE,
    SERVICE_SET_CHORE_ACTIVE,
)
from .exceptions import (
    InactiveChildrenError,
    NoActiveChildrenError,
    UnknownChildError,
    UnknownChildrenError,
    UnknownChoreError,
)
from .models import ChoresManagerConfigEntry

ADD_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1, max=100),
        ),
    }
)

ADD_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TITLE): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1, max=100),
        ),
        vol.Required(ATTR_CATEGORY): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1, max=100),
        ),
        vol.Required(ATTR_POINTS): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=100),
        ),
        vol.Optional(
            ATTR_ICON,
            default=DEFAULT_CHORE_ICON,
        ): cv.icon,
        vol.Optional(ATTR_SORT_ORDER): vol.All(
            vol.Coerce(int),
            vol.Range(min=0),
        ),
        vol.Optional(ATTR_CHILD_IDS): vol.All(
            cv.ensure_list,
            [
                vol.All(
                    cv.string,
                    str.strip,
                    vol.Length(min=1),
                )
            ],
            vol.Length(min=1),
        ),
    }
)

SET_CHILD_ACTIVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHILD_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
        vol.Required(ATTR_ACTIVE): cv.boolean,
    }
)

SET_CHORE_ACTIVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
        vol.Required(ATTR_ACTIVE): cv.boolean,
    }
)


def _get_loaded_entry(
    hass: HomeAssistant,
) -> ChoresManagerConfigEntry:
    """Return the loaded Chores Manager config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)

    if len(entries) != 1 or entries[0].state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="integration_not_loaded",
        )

    return cast(ChoresManagerConfigEntry, entries[0])


async def async_setup_services(
    hass: HomeAssistant,
    config: ConfigType,
) -> None:
    """Register Chores Manager actions."""

    async def async_handle_add_child(call: ServiceCall) -> None:
        """Handle the add-child action."""
        entry = _get_loaded_entry(hass)
        name: str = call.data[ATTR_NAME]

        await entry.runtime_data.async_add_child(name)

    async def async_handle_add_chore(call: ServiceCall) -> None:
        """Handle the add-chore action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_add_chore(
                title=call.data[ATTR_TITLE],
                category=call.data[ATTR_CATEGORY],
                points=call.data[ATTR_POINTS],
                icon=call.data[ATTR_ICON],
                sort_order=call.data.get(ATTR_SORT_ORDER),
                child_ids=call.data.get(ATTR_CHILD_IDS),
            )
        except NoActiveChildrenError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_active_children",
            ) from err
        except UnknownChildrenError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_children",
                translation_placeholders={
                    "child_ids": ", ".join(err.child_ids),
                },
            ) from err
        except InactiveChildrenError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="inactive_children",
                translation_placeholders={
                    "child_ids": ", ".join(err.child_ids),
                },
            ) from err

    async def async_handle_set_child_active(call: ServiceCall) -> None:
        """Handle the set-child-active action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_set_child_active(
                call.data[ATTR_CHILD_ID],
                call.data[ATTR_ACTIVE],
            )
        except UnknownChildError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_child",
                translation_placeholders={
                    "child_id": err.child_id,
                },
            ) from err

    async def async_handle_set_chore_active(call: ServiceCall) -> None:
        """Handle the set-chore-active action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_set_chore_active(
                call.data[ATTR_CHORE_ID],
                call.data[ATTR_ACTIVE],
            )
        except UnknownChoreError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_chore",
                translation_placeholders={
                    "chore_id": err.chore_id,
                },
            ) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CHILD,
        async_handle_add_child,
        schema=ADD_CHILD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CHORE,
        async_handle_add_chore,
        schema=ADD_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CHILD_ACTIVE,
        async_handle_set_child_active,
        schema=SET_CHILD_ACTIVE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CHORE_ACTIVE,
        async_handle_set_chore_active,
        schema=SET_CHORE_ACTIVE_SCHEMA,
    )
