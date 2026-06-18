"""The adapter seam: the harness-normalized session and the adapter protocols."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from koalaty.schemas.adapters import HarvestedSession

if TYPE_CHECKING:
    from koalaty.schemas.tasks import Task

__all__ = ["Adapter", "HarvestedSession", "InvocableAdapter"]


@runtime_checkable
class Adapter(Protocol):
    """The per-harness interface koalaty drives.

    Every adapter must support `harvest`. Adapters that can also start a
    headless session implement `InvocableAdapter` instead; adapters that
    cannot invoke are manual-only (a human drives the session). An adapter
    never mints run-ids or knows pouch paths.
    """

    name: str

    def harvest(self, session_id: str) -> HarvestedSession:
        """Read a finished session and normalize it into a harvested session."""


@runtime_checkable
class InvocableAdapter(Adapter, Protocol):
    """An adapter that can start a headless session via `invoke`.

    `isinstance(adapter, InvocableAdapter)` is the type-safe way to check
    whether a harness supports automated invocation.
    """

    def invoke(self, task: Task, model: str) -> str:
        """Start a session for `task` with `model`; return its session id."""
