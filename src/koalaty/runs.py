"""Orchestration of automated and manual runs.

This module owns the run pipeline: validate → invoke → harvest → assemble
Result → write to pouch. The CLI and future frontends call here instead of
wiring the pipeline themselves.
"""

from datetime import UTC, datetime
from pathlib import Path

from koalaty import pouch
from koalaty.adapters import get_adapter, known_harnesses
from koalaty.adapters.base import InvocableAdapter
from koalaty.schemas.result import Result
from koalaty.schemas.tasks import Task, Turns

__all__ = ["run_automated"]


def run_automated(
    task: Task,
    harness: str,
    model: str,
    pouch_dir: Path,
    *,
    now: datetime | None = None,
) -> Result:
    """Run a task on a model in a harness and store the result in the pouch.

    Validates that the harness supports headless invocation and that the task
    is not interactive, then invokes the adapter, harvests the session,
    assembles the Result, and writes its run directory. Nothing is written on
    any rejection.
    """
    adapter = get_adapter(harness)
    if adapter is None:
        known = ", ".join(known_harnesses())
        msg = f"unknown harness {harness!r}; registered harnesses: {known}"
        raise ValueError(msg)

    if not isinstance(adapter, InvocableAdapter):
        msg = f"harness {harness!r} does not support headless invocation"
        raise TypeError(msg)

    if task.turns is Turns.interactive:
        msg = (
            f"task {task.id!r} is interactive (manual-only); drive it yourself and "
            f"use `start`/`harvest` instead of `run`"
        )
        raise ValueError(msg)

    started = now or datetime.now(UTC)
    run_id = pouch.new_run_id(pouch_dir, task.id, harness, model, started)

    session_id = adapter.invoke(task, model)
    harvested = adapter.harvest(session_id)

    result = Result(
        run_id=run_id,
        task=task.id,
        harness=harness,
        model=model,
        driver="koalaty",
        started_at=harvested.started_at,
        finished_at=harvested.finished_at,
        outcome=harvested.outcome,
        summary=harvested.summary,
        tags=task.tags,
        turns=task.turns,
    )
    pouch.write_run(pouch_dir, result, harvested.raw)

    return result
