"""Constants for the Chores Manager integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "chores_manager"
NAME: Final = "Chores Manager"

STORAGE_KEY: Final = f"{DOMAIN}.data"
STORAGE_VERSION: Final = 1

ATTR_CATEGORY: Final = "category"
ATTR_CHILD_IDS: Final = "child_ids"
ATTR_ICON: Final = "icon"
ATTR_NAME: Final = "name"
ATTR_POINTS: Final = "points"
ATTR_SORT_ORDER: Final = "sort_order"
ATTR_TITLE: Final = "title"

COMPLETION_MODE_INDEPENDENT: Final = "independent"

DEFAULT_CHORE_ICON: Final = "mdi:checkbox-marked-circle-outline"

SERVICE_ADD_CHILD: Final = "add_child"
SERVICE_ADD_CHORE: Final = "add_chore"

PLATFORMS: Final = (
    Platform.SENSOR,
    Platform.SWITCH,
)

UNIT_POINTS: Final = "points"

# datetime.date.weekday(): Monday is 0 and Saturday is 5.
WEEK_START_WEEKDAY: Final = 5
CHORES_LABEL_NAME: Final = "Chores"
CHORES_LABEL_ICON: Final = "mdi:format-list-checks"
CHORES_LABEL_DESCRIPTION: Final = "Chore assignment entities managed by Chores Manager."
