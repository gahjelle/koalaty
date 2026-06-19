"""Domain exceptions: shared base class and specific error types.

All custom exceptions inherit `KoalaError` so the CLI top-level handler can
catch domain errors uniformly while still allowing specific catches.
"""


class KoalaError(Exception):
    """Base class for all koalaty domain exceptions."""


class TaskLoadError(KoalaError):
    """A task bundle is missing, malformed, or fails validation."""


class TaskScaffoldError(KoalaError):
    """A task scaffold cannot be written (bad id or a colliding directory)."""


__all__ = ["KoalaError", "TaskLoadError", "TaskScaffoldError"]
