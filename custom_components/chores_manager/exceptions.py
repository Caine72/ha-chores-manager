"""Exceptions for Chores Manager."""


class ChoresManagerError(Exception):
    """Base exception for Chores Manager."""


class NoActiveChildrenError(ChoresManagerError):
    """Raised when no active children are available."""


class UnknownAssignmentError(ChoresManagerError):
    """Raised when an assignment ID does not exist."""

    def __init__(self, assignment_id: str) -> None:
        """Initialize the exception."""
        self.assignment_id = assignment_id
        super().__init__(assignment_id)


class UnknownChildrenError(ChoresManagerError):
    """Raised when one or more child IDs do not exist."""

    def __init__(self, child_ids: list[str]) -> None:
        """Initialize the exception."""
        self.child_ids = child_ids
        super().__init__(", ".join(child_ids))


class UnknownChildError(ChoresManagerError):
    """Raised when a child ID does not exist."""

    def __init__(self, child_id: str) -> None:
        """Initialize the exception."""
        self.child_id = child_id
        super().__init__(child_id)


class InactiveChildrenError(ChoresManagerError):
    """Raised when one or more selected children are inactive."""

    def __init__(self, child_ids: list[str]) -> None:
        """Initialize the exception."""
        self.child_ids = child_ids
        super().__init__(", ".join(child_ids))


class NoChoreUpdatesError(ChoresManagerError):
    """Raised when a chore update contains no editable fields."""


class UnknownChoreError(ChoresManagerError):
    """Raised when a chore ID does not exist."""

    def __init__(self, chore_id: str) -> None:
        """Initialize the exception."""
        self.chore_id = chore_id
        super().__init__(chore_id)
