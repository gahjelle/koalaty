"""The fake adapter: a hermetic harness needing no real CLI and no interaction."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from koalaty.adapters.base import HarvestedSession
from koalaty.schemas.result import Outcome

if TYPE_CHECKING:
    from koalaty.schemas.tasks import Task

__all__ = ["FakeAdapter"]

FAKE_STARTED_AT = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
FAKE_FINISHED_AT = datetime(2026, 1, 1, 12, 1, 30, tzinfo=UTC)
FAKE_SESSION_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"


class FakeAdapter:
    """An adapter that fabricates sessions in memory, walking invoke → harvest.

    Real adapters slot in unchanged: `invoke` returns a session id that
    `harvest` later resolves, exactly as a real harness round-trip would. The
    manual feed (`start` → `harvest`) skips `invoke` entirely: `start` hands you
    a concrete session id and `harvest` resolves only that id or ids from
    `invoke` — unknown ids are rejected.
    """

    name = "fake"

    def __init__(self) -> None:
        """Start with an empty in-memory store of fabricated sessions."""
        self._sessions: dict[str, dict[str, Any]] = {}

    def start(self, task: Task, model: str) -> str:
        """Return manual setup instructions naming the session id to harvest.

        The fake harness has no real CLI to drive, so it hands you a concrete
        session id up front; `harvest` resolves it without `invoke` ever running.
        """
        return (
            f"Fake harness (no real CLI to drive) for {task.id!r} on {model!r}.\n"
            f"Harvest the prepared session with:\n"
            f"    koalaty harvest <run-id> --session {FAKE_SESSION_ID}"
        )

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
        """Resolve a known session id into a deterministic harvested session.

        An id `invoke` minted resolves to its fabricated session; the id `start`
        hands out (`FAKE_SESSION_ID`) resolves to a manually-driven session.
        Any other id is rejected — `harvest` does not fabricate unknown ids.
        """
        if session_id == FAKE_SESSION_ID:
            raw: dict[str, Any] = {
                "session_id": session_id,
                "messages": [
                    {"role": "user", "content": "(manually driven session)"},
                    {"role": "assistant", "content": "Done — the task is complete."},
                ],
            }
            summary = f"Fake harvest of session {session_id!r} succeeded."
        elif session_id in self._sessions:
            raw = self._sessions[session_id]
            summary = f"Fake run of {raw['task']} on {raw['model']} succeeded."
        else:
            msg = f"unknown session {session_id!r}"
            raise ValueError(msg)
        return HarvestedSession(
            started_at=FAKE_STARTED_AT,
            finished_at=FAKE_FINISHED_AT,
            outcome=Outcome.success,
            summary=summary,
            raw=raw,
        )
