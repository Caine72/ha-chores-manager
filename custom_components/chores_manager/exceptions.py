"""Exceptions for Chores Manager."""


class ChoresManagerError(Exception):
    """Base exception for Chores Manager."""


class NoActiveChildrenError(ChoresManagerError):
    """Raised when no active children are available."""


class UnknownChildrenError(ChoresManagerError):
    """Raised when one or more child IDs do not exist."""

    def __init__(self, child_ids: list[str]) -> None:
        """Initialize the exception."""
        self.child_ids = child_ids
        super().__init__(", ".join(child_ids))


class InactiveChildrenError(ChoresManagerError):
    """Raised when one or more selected children are inactive."""

    def __init__(self, child_ids: list[str]) -> None:
        """Initialize the exception."""
        self.child_ids = child_ids
        super().__init__(", ".join(child_ids))
