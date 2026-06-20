"""The adapter seam: the harness-normalized session and the adapter protocols."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from koalaty.schemas.adapters import HarvestedSession

if TYPE_CHECKING:
    from koalaty.schemas.tasks import Task

__all__ = ["Adapter", "HarvestedSession", "InvocableAdapter"]


@runtime_checkable
class Adapter(Protocol):
    """The per-harness interface koalaty drives.

    Every adapter must support `start` and `harvest`, so every harness is
    manually drivable. Adapters that can also launch a headless session
    implement `InvocableAdapter` (adding `invoke`); adapters that cannot are
    manual-only (a human drives the session). An adapter never mints run-ids or
    knows pouch paths.
    """

    name: str

    def start(self, task: Task, model: str) -> str:
        """Return the harness-tailored manual setup instructions for `task`.

        The instructions tell a human how to drive the session by hand and how
        to find the finished session's id to `harvest` with. `start` never
        invokes the harness (see ADR-0009).
        """

    def harvest(self, session_id: str) -> HarvestedSession:
        """Read a finished session and normalize it into a harvested session."""


@runtime_checkable
class InvocableAdapter(Adapter, Protocol):
    """An adapter that can launch a headless session via `invoke`.

    `isinstance(adapter, InvocableAdapter)` is the type-safe way to check
    whether a harness supports automated invocation.
    """

    def invoke(self, task: Task, model: str) -> str:
        """Start a session for `task` with `model`; return its session id."""
