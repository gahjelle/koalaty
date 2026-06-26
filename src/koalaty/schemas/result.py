"""Result schemas: the `result.json` shape and its session-status enum."""

from datetime import datetime
from enum import StrEnum

from koalaty.schemas import FrozenModel
from koalaty.schemas.metrics import Metrics, ModelUsage
from koalaty.schemas.survey import Survey
from koalaty.schemas.tasks import Turns

__all__ = ["SCHEMA_VERSION", "Result", "SessionStatus"]

SCHEMA_VERSION = 1


class SessionStatus(StrEnum):
    """How the harness session *ended*, observed at harvest (see ADR-0014).

    Not a quality judgment: whether the task's done-condition was met is a
    separate verdict produced later by paws/survey.
    """

    completed = "completed"
    interrupted = "interrupted"
    errored = "errored"


class Result(FrozenModel):
    """The normalized, stored record a run produces, serialized as `result.json`.

    Authoritative source of every run field; the run-id directory name is only a
    human-readable label and is never parsed for information (see ADR-0003).
    """

    schema_version: int = SCHEMA_VERSION
    run_id: str
    task: str
    harness: str
    model: str
    driver: str
    started_at: datetime
    finished_at: datetime
    session_status: SessionStatus
    summary: str
    metrics: Metrics
    models_seen: list[ModelUsage]
    tags: list[str]
    turns: Turns
    joey: bool = False
    survey: Survey | None = None
