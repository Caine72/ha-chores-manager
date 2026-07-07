"""Persistent storage for Chores Manager."""

import asyncio
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import NotRequired, TypedDict

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    COMPLETION_MODE_INDEPENDENT,
    STORAGE_KEY,
    STORAGE_VERSION,
    WEEK_START_WEEKDAY,
)
from .exceptions import (
    InactiveChildrenError,
    NoActiveChildrenError,
    UnknownChildrenError,
)

type StoreListener = Callable[[], None]


class ChildData(TypedDict):
    """Stored child data."""

    name: str
    active: bool


class ChoreData(TypedDict):
    """Stored chore definition."""

    title: str
    category: str
    points: int
    icon: str
    active: bool
    sort_order: int
    completion_mode: str


class AssignmentData(TypedDict):
    """Stored assignment between a child and chore."""

    child_id: str
    chore_id: str
    active: bool


class CompletionData(TypedDict):
    """Stored chore completion."""

    completed_at: str
    local_date: str

    child_id: str
    chore_id: str
    assignment_id: str

    child_name: str
    chore_title: str
    category: str
    points: int


class ChoresManagerData(TypedDict):
    """Stored Chores Manager data."""

    next_child_id: int
    next_chore_id: int
    next_assignment_id: int
    next_completion_id: int

    children: dict[str, ChildData]
    chores: dict[str, ChoreData]
    assignments: dict[str, AssignmentData]
    completions: dict[str, CompletionData]
    label_initialized_assignment_ids: NotRequired[list[str]]


def create_empty_data() -> ChoresManagerData:
    """Create the initial empty storage structure."""
    return {
        "next_child_id": 1,
        "next_chore_id": 1,
        "next_assignment_id": 1,
        "next_completion_id": 1,
        "children": {},
        "chores": {},
        "assignments": {},
        "completions": {},
        "label_initialized_assignment_ids": [],
    }


class ChoresManagerStore:
    """Manage persistent Chores Manager data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the store."""
        self._store: Store[ChoresManagerData] = Store(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
        )
        self._lock = asyncio.Lock()
        self._listeners: set[StoreListener] = set()
        self.data = create_empty_data()

    async def async_load(self) -> None:
        """Load data from persistent storage."""
        stored_data = await self._store.async_load()

        if stored_data is None:
            await self.async_save()
            return

        self.data = stored_data
        data_changed = False

        if "label_initialized_assignment_ids" not in self.data:
            self.data["label_initialized_assignment_ids"] = []
            data_changed = True

        if self._prune_old_completions(dt_util.now().date()):
            data_changed = True

        if data_changed:
            await self.async_save()

    async def async_save(self) -> None:
        """Persist the current data and notify listeners."""
        await self._store.async_save(self.data)
        self._async_notify_listeners()

    async def async_handle_local_midnight(self, now: datetime) -> None:
        """Refresh date-bound state and prune at the chore-week boundary."""
        if now.date().weekday() == WEEK_START_WEEKDAY:
            async with self._lock:
                if self._prune_old_completions(now.date()):
                    await self.async_save()
                    return

        self._async_notify_listeners()

    def is_assignment_label_initialized(
        self,
        assignment_id: str,
    ) -> bool:
        """Return whether the default chore label was initialized."""
        return assignment_id in self.data.get(
            "label_initialized_assignment_ids",
            [],
        )

    async def async_mark_assignment_label_initialized(
        self,
        assignment_id: str,
    ) -> None:
        """Record that the default chore label was initialized."""
        async with self._lock:
            initialized_ids = self.data.setdefault(
                "label_initialized_assignment_ids",
                [],
            )

            if assignment_id in initialized_ids:
                return

            initialized_ids.append(assignment_id)
            await self.async_save()

    @callback
    def async_add_listener(
        self,
        listener: StoreListener,
    ) -> Callable[[], None]:
        """Register a listener for stored data changes."""
        self._listeners.add(listener)

        @callback
        def remove_listener() -> None:
            """Remove the listener."""
            self._listeners.discard(listener)

        return remove_listener

    @callback
    def _async_notify_listeners(self) -> None:
        """Notify registered listeners that data changed."""
        for listener in tuple(self._listeners):
            listener()

    async def async_add_child(self, name: str) -> str:
        """Add a child and return its stable ID."""
        async with self._lock:
            child_number = self.data["next_child_id"]
            child_id = f"kid_{child_number}"

            self.data["children"][child_id] = {
                "name": name,
                "active": True,
            }
            self.data["next_child_id"] = child_number + 1

            await self.async_save()

        return child_id

    async def async_add_chore(
        self,
        *,
        title: str,
        category: str,
        points: int,
        icon: str,
        sort_order: int | None = None,
        child_ids: list[str] | None = None,
    ) -> tuple[str, list[str]]:
        """Add a reusable chore and assignments."""
        async with self._lock:
            selected_child_ids = self._resolve_child_ids(child_ids)

            chore_number = self.data["next_chore_id"]
            chore_id = f"chore_{chore_number}"

            self.data["chores"][chore_id] = {
                "title": title,
                "category": category,
                "points": points,
                "icon": icon,
                "active": True,
                "sort_order": (
                    sort_order if sort_order is not None else chore_number * 10
                ),
                "completion_mode": COMPLETION_MODE_INDEPENDENT,
            }
            self.data["next_chore_id"] = chore_number + 1

            assignment_ids: list[str] = []

            for child_id in selected_child_ids:
                assignment_number = self.data["next_assignment_id"]
                assignment_id = f"assignment_{assignment_number}"

                self.data["assignments"][assignment_id] = {
                    "child_id": child_id,
                    "chore_id": chore_id,
                    "active": True,
                }
                self.data["next_assignment_id"] = assignment_number + 1
                assignment_ids.append(assignment_id)

            await self.async_save()

        return chore_id, assignment_ids

    async def async_complete_assignment(self, assignment_id: str) -> str:
        """Complete an assignment for today."""
        async with self._lock:
            existing_completion_id = self._get_today_completion_id(assignment_id)
            if existing_completion_id is not None:
                return existing_completion_id

            assignment = self.data["assignments"][assignment_id]
            child = self.data["children"][assignment["child_id"]]
            chore = self.data["chores"][assignment["chore_id"]]

            if not assignment["active"]:
                raise ValueError(f"Assignment {assignment_id} is inactive")

            if not child["active"]:
                raise ValueError(f"Child {assignment['child_id']} is inactive")

            if not chore["active"]:
                raise ValueError(f"Chore {assignment['chore_id']} is inactive")

            completion_number = self.data["next_completion_id"]
            completion_id = f"completion_{completion_number}"

            self.data["completions"][completion_id] = {
                "completed_at": dt_util.utcnow().isoformat(),
                "local_date": dt_util.now().date().isoformat(),
                "child_id": assignment["child_id"],
                "chore_id": assignment["chore_id"],
                "assignment_id": assignment_id,
                "child_name": child["name"],
                "chore_title": chore["title"],
                "category": chore["category"],
                "points": chore["points"],
            }
            self.data["next_completion_id"] = completion_number + 1

            await self.async_save()

        return completion_id

    async def async_uncomplete_assignment(
        self,
        assignment_id: str,
    ) -> bool:
        """Remove today's completion for an assignment."""
        async with self._lock:
            completion_ids = [
                completion_id
                for completion_id, completion in self.data["completions"].items()
                if completion["assignment_id"] == assignment_id
                and completion["local_date"] == dt_util.now().date().isoformat()
            ]

            if not completion_ids:
                return False

            for completion_id in completion_ids:
                del self.data["completions"][completion_id]

            await self.async_save()

        return True

    def is_assignment_completed_today(
        self,
        assignment_id: str,
    ) -> bool:
        """Return whether an assignment is completed today."""
        return self._get_today_completion_id(assignment_id) is not None

    def _get_today_completion_id(
        self,
        assignment_id: str,
    ) -> str | None:
        """Return today's completion ID for an assignment."""
        today = dt_util.now().date().isoformat()

        return next(
            (
                completion_id
                for completion_id, completion in self.data["completions"].items()
                if completion["assignment_id"] == assignment_id
                and completion["local_date"] == today
            ),
            None,
        )

    def get_current_week_bounds(
        self,
        reference_date: date | None = None,
    ) -> tuple[date, date]:
        """Return the chore-week bounds containing a date."""
        current_date = reference_date or dt_util.now().date()
        days_since_week_start = (current_date.weekday() - WEEK_START_WEEKDAY) % 7

        week_start = current_date - timedelta(days=days_since_week_start)
        week_end = week_start + timedelta(days=6)

        return week_start, week_end

    def get_current_week_points(self, child_id: str) -> int:
        """Return the points earned by a child this chore week."""
        week_start, week_end = self.get_current_week_bounds()

        return sum(
            completion["points"]
            for completion in self.data["completions"].values()
            if completion["child_id"] == child_id
            and week_start <= date.fromisoformat(completion["local_date"]) <= week_end
        )

    def _prune_old_completions(self, reference_date: date) -> bool:
        """Remove completions older than the retained two chore weeks."""
        current_week_start, _ = self.get_current_week_bounds(reference_date)
        retention_start = current_week_start - timedelta(days=7)
        completion_ids_to_remove = [
            completion_id
            for completion_id, completion in self.data["completions"].items()
            if date.fromisoformat(completion["local_date"]) < retention_start
        ]

        for completion_id in completion_ids_to_remove:
            del self.data["completions"][completion_id]

        return bool(completion_ids_to_remove)

    def _resolve_child_ids(
        self,
        child_ids: list[str] | None,
    ) -> list[str]:
        """Resolve and validate children selected for a chore."""
        children = self.data["children"]

        if child_ids is None:
            active_child_ids = [
                child_id for child_id, child in children.items() if child["active"]
            ]

            if not active_child_ids:
                raise NoActiveChildrenError

            return active_child_ids

        selected_child_ids = list(dict.fromkeys(child_ids))

        unknown_child_ids = [
            child_id for child_id in selected_child_ids if child_id not in children
        ]
        if unknown_child_ids:
            raise UnknownChildrenError(unknown_child_ids)

        inactive_child_ids = [
            child_id
            for child_id in selected_child_ids
            if not children[child_id]["active"]
        ]
        if inactive_child_ids:
            raise InactiveChildrenError(inactive_child_ids)

        return selected_child_ids
