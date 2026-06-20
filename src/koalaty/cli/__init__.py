"""Command-line interface package: shared parameter types and validators.

The per-area command modules (`runs`, `compare`, `task`, `config`) import the
shared cyclopts parameter types and validators from here; `main` assembles them
into the application. Keeping the shared CLI vocabulary in one place lets each
command module stay focused on its own handlers.
"""

import re
from typing import Annotated

from cyclopts import Parameter

from koalaty import config as koalaty_config
from koalaty.adapters import known_harnesses
from koalaty.tasks import list_task_ids

__all__ = [
    "HarnessParam",
    "ModelParam",
    "TaskParam",
    "validate_harness",
    "validate_model",
    "validate_task",
]

MODEL_NAME_RE = re.compile(koalaty_config.config.model.name_pattern)


def validate_harness(_type: type, value: str) -> None:
    """Reject harnesses without a registered adapter."""
    if value not in known_harnesses():
        known = ", ".join(known_harnesses())
        msg = f"unknown harness {value!r}; registered harnesses: {known}"
        raise ValueError(msg)


def validate_model(_type: type, value: str) -> None:
    """Reject model names that are not dash-free canonical slugs."""
    if not MODEL_NAME_RE.fullmatch(value):
        msg = (
            f"model {value!r} must match {MODEL_NAME_RE.pattern} (a-z, 0-9; no dashes)"
        )
        raise ValueError(msg)


def validate_task(_type: type, value: str) -> None:
    """Reject task names not found in `config.tasks`."""
    task_ids = list_task_ids(koalaty_config.config.tasks)
    if value not in task_ids:
        ids = ", ".join(task_ids)
        msg = (
            f"Choose from: {ids}."
            if ids
            else "No tasks found, use 'koalaty task' to create tasks"
        )
        raise ValueError(msg)


type HarnessParam = Annotated[str, Parameter(validator=validate_harness)]
type ModelParam = Annotated[str, Parameter(validator=validate_model)]
type TaskParam = Annotated[str, Parameter(validator=validate_task)]
