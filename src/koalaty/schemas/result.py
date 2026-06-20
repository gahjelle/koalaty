"""Result schemas: the `result.json` shape and its outcome enum."""

from datetime import datetime
from enum import StrEnum

from koalaty.schemas import FrozenModel
from koalaty.schemas.survey import Survey
from koalaty.schemas.tasks import Turns

__all__ = ["SCHEMA_VERSION", "Outcome", "Result"]

SCHEMA_VERSION = 1


class Outcome(StrEnum):
    """Whether a run reached its done-condition."""

    success = "success"
    failure = "failure"


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
    outcome: Outcome
    summary: str
    tags: list[str]
    turns: Turns
    survey: Survey | None = None
