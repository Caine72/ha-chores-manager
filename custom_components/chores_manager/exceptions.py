"""Exceptions for Chores Manager."""


class ChoresManagerError(Exception):
    """Base exception for Chores Manager."""


class NoActiveChildrenError(ChoresManagerError):
    """Raised when no active children are available."""


class DuplicateAssignmentError(ChoresManagerError):
    """Raised when a child-to-chore assignment already exists."""

    def __init__(
        self,
        child_id: str,
        chore_id: str,
        assignment_id: str,
    ) -> None:
        """Initialize the exception."""
        self.child_id = child_id
        self.chore_id = chore_id
        self.assignment_id = assignment_id
        super().__init__(assignment_id)


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


class InactiveChildError(ChoresManagerError):
    """Raised when a selected child is inactive."""

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


class InactiveChoreError(ChoresManagerError):
    """Raised when a selected chore is inactive."""

    def __init__(self, chore_id: str) -> None:
        """Initialize the exception."""
        self.chore_id = chore_id
        super().__init__(chore_id)


class NoChoreUpdatesError(ChoresManagerError):
    """Raised when a chore update contains no editable fields."""


class UnknownChoreError(ChoresManagerError):
    """Raised when a chore ID does not exist."""

    def __init__(self, chore_id: str) -> None:
        """Initialize the exception."""
        self.chore_id = chore_id
        super().__init__(chore_id)


class DuplicateChoreIdsError(ChoresManagerError):
    """Raised when a bulk request repeats one or more chore IDs."""

    def __init__(self, chore_ids: list[str]) -> None:
        """Initialize the exception."""
        self.chore_ids = chore_ids
        super().__init__(", ".join(chore_ids))


class ExistingAssignmentsError(ChoresManagerError):
    """Raised when bulk assignment relationships already exist."""

    def __init__(self, chore_ids: list[str]) -> None:
        """Initialize the exception."""
        self.chore_ids = chore_ids
        super().__init__(", ".join(chore_ids))


class MissingAssignmentsError(ChoresManagerError):
    """Raised when requested child-to-chore assignments do not exist."""

    def __init__(self, chore_ids: list[str]) -> None:
        """Initialize the exception."""
        self.chore_ids = chore_ids
        super().__init__(", ".join(chore_ids))


class InactiveChoresError(ChoresManagerError):
    """Raised when one or more selected chores are inactive."""

    def __init__(self, chore_ids: list[str]) -> None:
        """Initialize the exception."""
        self.chore_ids = chore_ids
        super().__init__(", ".join(chore_ids))


class UnknownChoresError(ChoresManagerError):
    """Raised when one or more chore IDs do not exist."""

    def __init__(self, chore_ids: list[str]) -> None:
        """Initialize the exception."""
        self.chore_ids = chore_ids
        super().__init__(", ".join(chore_ids))
