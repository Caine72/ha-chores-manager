"""Actions provided by Chores Manager."""

from functools import partial
from typing import cast

import voluptuous as vol

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_ACTIVE,
    ATTR_ASSIGNMENT_ID,
    ATTR_CATEGORY,
    ATTR_CHILD_ID,
    ATTR_CHILD_IDS,
    ATTR_CHORE_ID,
    ATTR_CHORE_IDS,
    ATTR_ICON,
    ATTR_NAME,
    ATTR_POINTS,
    ATTR_SORT_ORDER,
    ATTR_TITLE,
    DEFAULT_CHORE_ICON,
    DOMAIN,
    SERVICE_ADD_ASSIGNMENT,
    SERVICE_ADD_CHILD,
    SERVICE_ADD_CHORE,
    SERVICE_ASSIGN_CHORES_TO_CHILD,
    SERVICE_DELETE_ASSIGNMENT,
    SERVICE_DELETE_CHILD,
    SERVICE_DELETE_CHORE,
    SERVICE_SET_ASSIGNMENT_ACTIVE,
    SERVICE_SET_CHILD_ACTIVE,
    SERVICE_SET_CHORE_ACTIVE,
    SERVICE_UPDATE_CHILD,
    SERVICE_UPDATE_CHORE,
)
from .exceptions import (
    DuplicateAssignmentError,
    DuplicateChoreIdsError,
    ExistingAssignmentsError,
    InactiveChildError,
    InactiveChildrenError,
    InactiveChoreError,
    InactiveChoresError,
    NoActiveChildrenError,
    NoChoreUpdatesError,
    UnknownAssignmentError,
    UnknownChildError,
    UnknownChildrenError,
    UnknownChoreError,
    UnknownChoresError,
)
from .models import ChoresManagerConfigEntry

ADD_ASSIGNMENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHILD_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
        vol.Required(ATTR_CHORE_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
    }
)

ASSIGN_CHORES_TO_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHILD_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
        vol.Required(ATTR_CHORE_IDS): vol.All(
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

ADD_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1, max=100),
        ),
    }
)

UPDATE_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHILD_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
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

DELETE_ASSIGNMENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ASSIGNMENT_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
    }
)

DELETE_CHILD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHILD_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
    }
)

DELETE_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
    }
)

SET_ASSIGNMENT_ACTIVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ASSIGNMENT_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
        vol.Required(ATTR_ACTIVE): cv.boolean,
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

UPDATE_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1),
        ),
        vol.Optional(ATTR_TITLE): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1, max=100),
        ),
        vol.Optional(ATTR_CATEGORY): vol.All(
            cv.string,
            str.strip,
            vol.Length(min=1, max=100),
        ),
        vol.Optional(ATTR_POINTS): vol.All(
            vol.Coerce(int),
            vol.Range(min=1, max=100),
        ),
        vol.Optional(ATTR_ICON): cv.icon,
        vol.Optional(ATTR_SORT_ORDER): vol.All(
            vol.Coerce(int),
            vol.Range(min=0),
        ),
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


def _async_remove_registry_entry(
    hass: HomeAssistant,
    domain: str,
    unique_id: str,
) -> None:
    """Remove an entity registry entry by unique ID if it exists."""
    entity_registry = er.async_get(hass)
    entity_id = entity_registry.async_get_entity_id(domain, DOMAIN, unique_id)

    if entity_id is not None:
        entity_registry.async_remove(entity_id)


def _async_remove_assignment_registry_entries(
    hass: HomeAssistant,
    assignment_ids: list[str],
) -> None:
    """Remove assignment switch registry entries by assignment IDs."""
    for assignment_id in assignment_ids:
        _async_remove_registry_entry(hass, SWITCH_DOMAIN, assignment_id)


async def _async_handle_delete_assignment(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Handle the delete-assignment action."""
    entry = _get_loaded_entry(hass)
    assignment_id: str = call.data[ATTR_ASSIGNMENT_ID]

    try:
        await entry.runtime_data.async_delete_assignment(assignment_id)
    except UnknownAssignmentError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_assignment",
            translation_placeholders={
                "assignment_id": err.assignment_id,
            },
        ) from err

    _async_remove_registry_entry(hass, SWITCH_DOMAIN, assignment_id)


async def _async_handle_delete_child(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Handle the delete-child action."""
    entry = _get_loaded_entry(hass)
    child_id: str = call.data[ATTR_CHILD_ID]

    try:
        assignment_ids = await entry.runtime_data.async_delete_child(child_id)
    except UnknownChildError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_child",
            translation_placeholders={
                "child_id": err.child_id,
            },
        ) from err

    _async_remove_registry_entry(hass, SENSOR_DOMAIN, f"{child_id}_weekly_points")
    _async_remove_assignment_registry_entries(hass, assignment_ids)


async def _async_handle_delete_chore(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Handle the delete-chore action."""
    entry = _get_loaded_entry(hass)
    chore_id: str = call.data[ATTR_CHORE_ID]

    try:
        assignment_ids = await entry.runtime_data.async_delete_chore(chore_id)
    except UnknownChoreError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_chore",
            translation_placeholders={
                "chore_id": err.chore_id,
            },
        ) from err

    _async_remove_assignment_registry_entries(hass, assignment_ids)


async def _async_handle_assign_chores_to_child(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Handle the atomic assign-chores-to-child action."""
    entry = _get_loaded_entry(hass)

    try:
        await entry.runtime_data.async_assign_chores_to_child(
            call.data[ATTR_CHILD_ID],
            call.data[ATTR_CHORE_IDS],
        )
    except UnknownChildError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_child",
            translation_placeholders={"child_id": err.child_id},
        ) from err
    except InactiveChildError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="inactive_child",
            translation_placeholders={"child_id": err.child_id},
        ) from err
    except DuplicateChoreIdsError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="duplicate_chore_ids",
            translation_placeholders={"chore_ids": ", ".join(err.chore_ids)},
        ) from err
    except UnknownChoresError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_chores",
            translation_placeholders={"chore_ids": ", ".join(err.chore_ids)},
        ) from err
    except InactiveChoresError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="inactive_chores",
            translation_placeholders={"chore_ids": ", ".join(err.chore_ids)},
        ) from err
    except ExistingAssignmentsError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="existing_assignments",
            translation_placeholders={"chore_ids": ", ".join(err.chore_ids)},
        ) from err


async def async_setup_services(
    hass: HomeAssistant,
    config: ConfigType,
) -> None:
    """Register Chores Manager actions."""

    async def async_handle_add_assignment(call: ServiceCall) -> None:
        """Handle the add-assignment action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_add_assignment(
                call.data[ATTR_CHILD_ID],
                call.data[ATTR_CHORE_ID],
            )
        except UnknownChildError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_child",
                translation_placeholders={
                    "child_id": err.child_id,
                },
            ) from err
        except UnknownChoreError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_chore",
                translation_placeholders={
                    "chore_id": err.chore_id,
                },
            ) from err
        except DuplicateAssignmentError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="duplicate_assignment",
                translation_placeholders={
                    "assignment_id": err.assignment_id,
                    "child_id": err.child_id,
                    "chore_id": err.chore_id,
                },
            ) from err
        except InactiveChildError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="inactive_child",
                translation_placeholders={
                    "child_id": err.child_id,
                },
            ) from err
        except InactiveChoreError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="inactive_chore",
                translation_placeholders={
                    "chore_id": err.chore_id,
                },
            ) from err

    async def async_handle_add_child(call: ServiceCall) -> None:
        """Handle the add-child action."""
        entry = _get_loaded_entry(hass)
        name: str = call.data[ATTR_NAME]

        await entry.runtime_data.async_add_child(name)

    async def async_handle_update_child(call: ServiceCall) -> None:
        """Handle the update-child action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_update_child(
                call.data[ATTR_CHILD_ID],
                call.data[ATTR_NAME],
            )
        except UnknownChildError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_child",
                translation_placeholders={
                    "child_id": err.child_id,
                },
            ) from err

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

    async def async_handle_set_assignment_active(call: ServiceCall) -> None:
        """Handle the set-assignment-active action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_set_assignment_active(
                call.data[ATTR_ASSIGNMENT_ID],
                call.data[ATTR_ACTIVE],
            )
        except UnknownAssignmentError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_assignment",
                translation_placeholders={
                    "assignment_id": err.assignment_id,
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

    async def async_handle_update_chore(call: ServiceCall) -> None:
        """Handle the update-chore action."""
        entry = _get_loaded_entry(hass)

        try:
            await entry.runtime_data.async_update_chore(
                call.data[ATTR_CHORE_ID],
                title=call.data.get(ATTR_TITLE),
                category=call.data.get(ATTR_CATEGORY),
                points=call.data.get(ATTR_POINTS),
                icon=call.data.get(ATTR_ICON),
                sort_order=call.data.get(ATTR_SORT_ORDER),
            )
        except NoChoreUpdatesError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_chore_updates",
            ) from err
        except UnknownChoreError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_chore",
                translation_placeholders={
                    "chore_id": err.chore_id,
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
        SERVICE_ADD_ASSIGNMENT,
        async_handle_add_assignment,
        schema=ADD_ASSIGNMENT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ASSIGN_CHORES_TO_CHILD,
        partial(_async_handle_assign_chores_to_child, hass),
        schema=ASSIGN_CHORES_TO_CHILD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CHILD,
        async_handle_add_child,
        schema=ADD_CHILD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_CHILD,
        async_handle_update_child,
        schema=UPDATE_CHILD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CHORE,
        async_handle_add_chore,
        schema=ADD_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_ASSIGNMENT,
        partial(_async_handle_delete_assignment, hass),
        schema=DELETE_ASSIGNMENT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_CHILD,
        partial(_async_handle_delete_child, hass),
        schema=DELETE_CHILD_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_CHORE,
        partial(_async_handle_delete_chore, hass),
        schema=DELETE_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ASSIGNMENT_ACTIVE,
        async_handle_set_assignment_active,
        schema=SET_ASSIGNMENT_ACTIVE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CHILD_ACTIVE,
        async_handle_set_child_active,
        schema=SET_CHILD_ACTIVE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_CHORE,
        async_handle_update_chore,
        schema=UPDATE_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_CHORE_ACTIVE,
        async_handle_set_chore_active,
        schema=SET_CHORE_ACTIVE_SCHEMA,
    )
