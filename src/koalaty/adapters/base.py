"""The adapter seam: the harness-normalized session and the adapter protocol."""

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from koalaty.models import FrozenModel
from koalaty.result import Outcome


class HarvestedSession(FrozenModel):
    """A harness session normalized by an adapter, free of any run identity.

    Carries only what the harness reported; the orchestrator supplies run-id,
    task, harness, model, and the derived driver when assembling the result.
    """

    started_at: datetime
    finished_at: datetime
    outcome: Outcome
    summary: str
    raw: dict[str, Any]


@runtime_checkable
class Adapter(Protocol):
    """The per-harness interface koalaty drives.

    `invoke` is optional capability (absent ⇒ the harness is manual-only);
    `harvest` is required. An adapter never mints run-ids or knows pouch paths.
    """

    name: str

    def invoke(self, task: str, model: str) -> str:
        """Start a session for `task` with `model`; return its session id."""

    def harvest(self, session_id: str) -> HarvestedSession:
        """Read a finished session and normalize it into a harvested session."""
