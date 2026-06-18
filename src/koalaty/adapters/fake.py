"""The fake adapter: a hermetic harness needing no real CLI and no interaction."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from koalaty.adapters.base import HarvestedSession
from koalaty.result import Outcome

if TYPE_CHECKING:
    from koalaty.tasks import Task

# Fixed fabricated timestamps so harvested sessions are deterministic.
_FAKE_STARTED_AT = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
_FAKE_FINISHED_AT = datetime(2026, 1, 1, 12, 1, 30, tzinfo=UTC)


class FakeAdapter:
    """An adapter that fabricates sessions in memory, walking invoke → harvest.

    Real adapters slot in unchanged: `invoke` returns a session id that
    `harvest` later resolves, exactly as a real harness round-trip would.
    """

    name = "fake"

    def __init__(self) -> None:
        """Start with an empty in-memory store of fabricated sessions."""
        self._sessions: dict[str, dict[str, Any]] = {}

    def invoke(self, task: Task, model: str) -> str:
        """Fabricate a session from the task's opening prompt; return its id."""
        session_id = uuid4().hex
        self._sessions[session_id] = {
            "task": task.id,
            "model": model,
            "messages": [
                {"role": "user", "content": task.prompts[0]},
                {"role": "assistant", "content": "Done — the task is complete."},
            ],
        }
        return session_id

    def harvest(self, session_id: str) -> HarvestedSession:
        """Resolve a fabricated session into a deterministic harvested session."""
        raw = self._sessions[session_id]
        return HarvestedSession(
            started_at=_FAKE_STARTED_AT,
            finished_at=_FAKE_FINISHED_AT,
            outcome=Outcome.success,
            summary=f"Fake run of {raw['task']} on {raw['model']} succeeded.",
            raw=raw,
        )
