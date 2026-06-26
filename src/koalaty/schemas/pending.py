"""Pending-run schema: the `pending.json` shape a manual run wears before harvest.

A manual run is *pending* between `start` and `harvest`. It is stored as its
own `pending.json` so a `result.json` always means a completed run (ADR-0008).
A `PendingRun` carries only what `start` knows; the harvest-derived fields
(session status, summary, timestamps, metrics) appear on `Result`, never here.
"""

from datetime import datetime

from koalaty.schemas import FrozenModel
from koalaty.schemas.result import SCHEMA_VERSION
from koalaty.schemas.tasks import Turns

__all__ = ["PendingRun"]


class PendingRun(FrozenModel):
    """A manual run awaiting its session, serialized as `pending.json`.

    Written by `start` and removed by `harvest`. `driver` is always `human`
    for a manual run (ADR-0009); fields that `start` knows ride through to
    the assembled `Result` so the harvested session need not carry them.
    """

    schema_version: int = SCHEMA_VERSION
    run_id: str
    task: str
    harness: str
    model: str
    driver: str
    turns: Turns
    tags: list[str]
    gum_commit: str | None = None
    joey: bool = False
    created_at: datetime
