"""Adapter schemas: the harvested session shape shared by all adapters."""

from datetime import datetime
from typing import Any

from koalaty.schemas import FrozenModel
from koalaty.schemas.result import Outcome

__all__ = ["HarvestedSession"]


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
