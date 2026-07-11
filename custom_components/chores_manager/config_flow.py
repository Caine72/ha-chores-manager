"""Config and options flows for the Chores Manager integration."""

from typing import Any, cast

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult, OptionsFlow
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import selector

from .const import (
    ATTR_ACTIVE,
    ATTR_CATEGORY,
    ATTR_CHILD_ID,
    ATTR_CHORE_ID,
    ATTR_ICON,
    ATTR_NAME,
    ATTR_POINTS,
    ATTR_SORT_ORDER,
    ATTR_TITLE,
    DEFAULT_CHORE_ICON,
    DOMAIN,
    NAME,
    SERVICE_ADD_CHILD,
    SERVICE_ADD_CHORE,
    SERVICE_DELETE_CHILD,
    SERVICE_DELETE_CHORE,
    SERVICE_SET_CHILD_ACTIVE,
    SERVICE_SET_CHORE_ACTIVE,
    SERVICE_UPDATE_CHILD,
    SERVICE_UPDATE_CHORE,
)
from .models import ChoresManagerConfigEntry

ADVANCED_CHORE_OPTIONS = "advanced_chore_options"


class ChoresManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chores Manager."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the Chores Manager options flow."""
        return ChoresManagerOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle setup initiated by the user."""
        if user_input is not None:
            return self.async_create_entry(
                title=NAME,
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )


def _stable_id_sort_key(stable_id: str) -> tuple[str, int, str]:
    """Return a deterministic sort key for integration stable IDs."""
    prefix, _, suffix = stable_id.rpartition("_")

    if suffix.isdecimal():
        return (prefix, int(suffix), "")

    return (prefix, -1, suffix)


class ChoresManagerOptionsFlow(OptionsFlow):
    """Manage Chores Manager data through Home Assistant's options UI."""

    _selected_child_id: str | None = None
    _selected_chore_id: str | None = None

    @property
    def _store(self):
        """Return the loaded Chores Manager store."""
        entry = cast(ChoresManagerConfigEntry, self.config_entry)
        return entry.runtime_data

    @staticmethod
    def _chore_action_data(user_input: dict[str, object]) -> dict[str, object]:
        """Flatten advanced chore form values for the existing action schema."""
        data = dict(user_input)
        data.update(data.pop(ADVANCED_CHORE_OPTIONS, {}))
        return data

    async def _async_call_action(
        self,
        action: str,
        data: dict[str, object],
    ) -> str | None:
        """Call an existing Chores Manager action and return a flow error key."""
        try:
            await self.hass.services.async_call(
                DOMAIN,
                action,
                data,
                blocking=True,
            )
        except ServiceValidationError as err:
            return err.translation_key or "unknown_error"

        return None

    def _child_options(self) -> list[selector.SelectOptionDict]:
        """Return child choices with stable IDs and activation state."""
        return [
            selector.SelectOptionDict(
                value=child_id,
                label=(
                    f"{child['name']} ({child_id})"
                    if child["active"]
                    else f"{child['name']} ({child_id}, inactive)"
                ),
            )
            for child_id, child in sorted(
                self._store.data["children"].items(),
                key=lambda item: _stable_id_sort_key(item[0]),
            )
        ]

    def _category_options(self) -> list[str]:
        """Return the categories already used by stored chores."""
        return sorted(
            {chore["category"] for chore in self._store.data["chores"].values()},
            key=str.casefold,
        )

    def _chore_options(self) -> list[selector.SelectOptionDict]:
        """Return chore choices with stable IDs and activation state."""
        return [
            selector.SelectOptionDict(
                value=chore_id,
                label=(
                    f"{chore['title']} ({chore['category']}, {chore['points']} points, {chore_id})"
                    if chore["active"]
                    else f"{chore['title']} ({chore['category']}, {chore['points']} points, {chore_id}, inactive)"
                ),
            )
            for chore_id, chore in sorted(
                self._store.data["chores"].items(),
                key=lambda item: _stable_id_sort_key(item[0]),
            )
        ]

    def _selected_child(self) -> dict[str, Any] | None:
        """Return the selected child, if it still exists."""
        if self._selected_child_id is None:
            return None

        return self._store.data["children"].get(self._selected_child_id)

    def _selected_chore(self) -> dict[str, Any] | None:
        """Return the selected chore, if it still exists."""
        if self._selected_chore_id is None:
            return None

        return self._store.data["chores"].get(self._selected_chore_id)

    async def async_step_init(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the management menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["children_menu", "chores_menu"],
        )

    async def async_step_children_menu(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show child management choices."""
        menu_options = ["add_child"]
        if self._child_options():
            menu_options.append("select_child")
        menu_options.append("init")

        return self.async_show_menu(
            step_id="children_menu",
            menu_options=menu_options,
        )

    async def async_step_chores_menu(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show chore management choices."""
        menu_options = ["add_chore"]
        if self._chore_options():
            menu_options.append("select_chore")
        menu_options.append("init")

        return self.async_show_menu(
            step_id="chores_menu",
            menu_options=menu_options,
        )

    async def async_step_add_child(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Add a child."""
        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._async_call_action(SERVICE_ADD_CHILD, user_input)
            if error is None:
                return await self.async_step_children_menu()
            errors["base"] = error

        return self.async_show_form(
            step_id="add_child",
            data_schema=vol.Schema({vol.Required(ATTR_NAME): selector.TextSelector()}),
            errors=errors,
        )

    async def async_step_select_child(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select a child to manage."""
        options = self._child_options()
        if not options:
            return await self.async_step_children_menu()

        if user_input is not None:
            child_id = user_input[ATTR_CHILD_ID]
            if child_id in self._store.data["children"]:
                self._selected_child_id = child_id
                return await self.async_step_child_actions()

            return self.async_show_form(
                step_id="select_child",
                data_schema=vol.Schema(
                    {
                        vol.Required(ATTR_CHILD_ID): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=options)
                        )
                    }
                ),
                errors={"base": "unknown_child"},
            )

        return self.async_show_form(
            step_id="select_child",
            data_schema=vol.Schema(
                {
                    vol.Required(ATTR_CHILD_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options)
                    )
                }
            ),
        )

    async def async_step_child_actions(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show actions for the selected child."""
        child = self._selected_child()
        if child is None:
            return await self.async_step_children_menu()

        return self.async_show_menu(
            step_id="child_actions",
            menu_options=[
                "edit_child",
                "deactivate_child" if child["active"] else "activate_child",
                "delete_child",
                "children_menu",
            ],
            description_placeholders={
                "name": child["name"],
                "child_id": self._selected_child_id or "",
                "status": "Active" if child["active"] else "Inactive",
            },
        )

    async def async_step_edit_child(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Edit the selected child."""
        child = self._selected_child()
        if child is None:
            return await self.async_step_children_menu()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._async_call_action(
                SERVICE_UPDATE_CHILD,
                {ATTR_CHILD_ID: self._selected_child_id, **user_input},
            )
            if error is None:
                return await self.async_step_child_actions()
            errors["base"] = error

        return self.async_show_form(
            step_id="edit_child",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ATTR_NAME, default=child["name"]
                    ): selector.TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_activate_child(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Activate the selected child."""
        if self._selected_child() is None:
            return await self.async_step_children_menu()

        error = await self._async_call_action(
            SERVICE_SET_CHILD_ACTIVE,
            {ATTR_CHILD_ID: self._selected_child_id, ATTR_ACTIVE: True},
        )
        if error is None:
            return await self.async_step_child_actions()

        return await self.async_step_child_actions()

    async def async_step_deactivate_child(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Deactivate the selected child."""
        if self._selected_child() is None:
            return await self.async_step_children_menu()

        error = await self._async_call_action(
            SERVICE_SET_CHILD_ACTIVE,
            {ATTR_CHILD_ID: self._selected_child_id, ATTR_ACTIVE: False},
        )
        if error is None:
            return await self.async_step_child_actions()

        return await self.async_step_child_actions()

    async def async_step_delete_child(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm deletion of the selected child."""
        child = self._selected_child()
        if child is None:
            return await self.async_step_children_menu()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._async_call_action(
                SERVICE_DELETE_CHILD,
                {ATTR_CHILD_ID: self._selected_child_id},
            )
            if error is None:
                self._selected_child_id = None
                return await self.async_step_children_menu()
            errors["base"] = error

        return self.async_show_form(
            step_id="delete_child",
            data_schema=vol.Schema({}),
            description_placeholders={"name": child["name"]},
            errors=errors,
        )

    async def async_step_add_chore(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Add a chore for all active children."""
        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._async_call_action(
                SERVICE_ADD_CHORE,
                self._chore_action_data(user_input),
            )
            if error is None:
                return await self.async_step_chores_menu()
            errors["base"] = error

        return self.async_show_form(
            step_id="add_chore",
            data_schema=self._chore_schema(),
            errors=errors,
        )

    async def async_step_select_chore(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select a chore to manage."""
        options = self._chore_options()
        if not options:
            return await self.async_step_chores_menu()

        if user_input is not None:
            chore_id = user_input[ATTR_CHORE_ID]
            if chore_id in self._store.data["chores"]:
                self._selected_chore_id = chore_id
                return await self.async_step_chore_actions()

            return self.async_show_form(
                step_id="select_chore",
                data_schema=self._chore_selector_schema(options),
                errors={"base": "unknown_chore"},
            )

        return self.async_show_form(
            step_id="select_chore",
            data_schema=self._chore_selector_schema(options),
        )

    async def async_step_chore_actions(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show actions for the selected chore."""
        chore = self._selected_chore()
        if chore is None:
            return await self.async_step_chores_menu()

        return self.async_show_menu(
            step_id="chore_actions",
            menu_options=[
                "edit_chore",
                "deactivate_chore" if chore["active"] else "activate_chore",
                "delete_chore",
                "chores_menu",
            ],
            description_placeholders={
                "title": chore["title"],
                "category": chore["category"],
                "points": str(chore["points"]),
                "chore_id": self._selected_chore_id or "",
                "status": "Active" if chore["active"] else "Inactive",
            },
        )

    async def async_step_edit_chore(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Edit the selected chore."""
        chore = self._selected_chore()
        if chore is None:
            return await self.async_step_chores_menu()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._async_call_action(
                SERVICE_UPDATE_CHORE,
                {
                    ATTR_CHORE_ID: self._selected_chore_id,
                    **self._chore_action_data(user_input),
                },
            )
            if error is None:
                return await self.async_step_chore_actions()
            errors["base"] = error

        return self.async_show_form(
            step_id="edit_chore",
            data_schema=self._chore_schema(chore),
            errors=errors,
        )

    async def async_step_activate_chore(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Activate the selected chore."""
        if self._selected_chore() is None:
            return await self.async_step_chores_menu()

        error = await self._async_call_action(
            SERVICE_SET_CHORE_ACTIVE,
            {ATTR_CHORE_ID: self._selected_chore_id, ATTR_ACTIVE: True},
        )
        if error is None:
            return await self.async_step_chore_actions()

        return await self.async_step_chore_actions()

    async def async_step_deactivate_chore(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Deactivate the selected chore."""
        if self._selected_chore() is None:
            return await self.async_step_chores_menu()

        error = await self._async_call_action(
            SERVICE_SET_CHORE_ACTIVE,
            {ATTR_CHORE_ID: self._selected_chore_id, ATTR_ACTIVE: False},
        )
        if error is None:
            return await self.async_step_chore_actions()

        return await self.async_step_chore_actions()

    async def async_step_delete_chore(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm deletion of the selected chore."""
        chore = self._selected_chore()
        if chore is None:
            return await self.async_step_chores_menu()

        errors: dict[str, str] = {}
        if user_input is not None:
            error = await self._async_call_action(
                SERVICE_DELETE_CHORE,
                {ATTR_CHORE_ID: self._selected_chore_id},
            )
            if error is None:
                self._selected_chore_id = None
                return await self.async_step_chores_menu()
            errors["base"] = error

        return self.async_show_form(
            step_id="delete_chore",
            data_schema=vol.Schema({}),
            description_placeholders={"title": chore["title"]},
            errors=errors,
        )

    @staticmethod
    def _chore_selector_schema(
        options: list[selector.SelectOptionDict],
    ) -> vol.Schema:
        """Build the chore selection schema."""
        return vol.Schema(
            {
                vol.Required(ATTR_CHORE_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options)
                )
            }
        )

    def _chore_schema(self, chore: dict[str, Any] | None = None) -> vol.Schema:
        """Build the chore add or edit schema."""
        defaults = chore or {}
        schema: dict[object, object] = {
            vol.Required(
                ATTR_TITLE, default=defaults.get(ATTR_TITLE, "")
            ): selector.TextSelector(),
            vol.Required(
                ATTR_CATEGORY, default=defaults.get(ATTR_CATEGORY, "")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=self._category_options(),
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                ATTR_POINTS, default=defaults.get(ATTR_POINTS, 1)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(ADVANCED_CHORE_OPTIONS): section(
                ChoresManagerOptionsFlow._advanced_chore_schema(defaults),
                SectionConfig(collapsed=True),
            ),
        }

        return vol.Schema(schema)

    @staticmethod
    def _advanced_chore_schema(defaults: dict[str, Any]) -> vol.Schema:
        """Build the advanced chore fields schema."""
        schema: dict[object, object] = {
            vol.Required(
                ATTR_ICON,
                default=defaults.get(ATTR_ICON, DEFAULT_CHORE_ICON),
            ): selector.IconSelector(),
        }
        sort_order = defaults.get(ATTR_SORT_ORDER)
        if sort_order is None:
            schema[vol.Optional(ATTR_SORT_ORDER)] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    mode=selector.NumberSelectorMode.BOX,
                )
            )
        else:
            schema[vol.Optional(ATTR_SORT_ORDER, default=sort_order)] = (
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            )

        return vol.Schema(schema)
