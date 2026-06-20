"""Domain exceptions: shared base class and specific error types.

All custom exceptions inherit `KoalatyError` so the CLI top-level handler can
catch domain errors uniformly while still allowing specific catches.
"""


class KoalatyError(Exception):
    """Base class for all koalaty domain exceptions."""


class TaskLoadError(KoalatyError):
    """A task bundle is missing, malformed, or fails validation."""


class TaskScaffoldError(KoalatyError):
    """A task scaffold cannot be written (bad id or a colliding directory)."""


class HarvestError(KoalatyError):
    """A manual run cannot be harvested (unknown or already-harvested run id)."""


__all__ = ["HarvestError", "KoalatyError", "TaskLoadError", "TaskScaffoldError"]
