"""Orchestration of automated and manual runs.

This module owns the run pipeline: validate → invoke → harvest → assemble
Result → write to pouch. The CLI and future frontends call here instead of
wiring the pipeline themselves.
"""

from datetime import UTC, datetime
from pathlib import Path

from koalaty import pouch
from koalaty.adapters import get_adapter, known_harnesses
from koalaty.adapters.base import Adapter, InvocableAdapter
from koalaty.schemas.pending import PendingRun
from koalaty.schemas.result import Result
from koalaty.schemas.tasks import Task, Turns
from koalaty.survey import Asker, collect_survey

__all__ = ["harvest_manual", "run_automated", "start_manual"]


def require_adapter(harness: str) -> Adapter:
    """Return the registered adapter for `harness`, or raise a friendly error."""
    adapter = get_adapter(harness)
    if adapter is None:
        known = ", ".join(known_harnesses())
        msg = f"unknown harness {harness!r}; registered harnesses: {known}"
        raise ValueError(msg)
    return adapter


def run_automated(
    task: Task,
    harness: str,
    model: str,
    *,
    pouch_dir: Path,
    joey: bool = False,
    now: datetime | None = None,
) -> Result:
    """Run a task on a model in a harness and store the result in the pouch.

    Validates that the harness supports headless invocation and that the task
    is not interactive, then invokes the adapter, harvests the session,
    assembles the Result, and writes its run directory. Nothing is written on
    any rejection. `joey` marks the result as a throwaway trial run.
    """
    adapter = require_adapter(harness)

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
    run_id = pouch.new_run_id(pouch_dir, task.id, harness, model=model, now=started)

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
        session_status=harvested.session_status,
        summary=harvested.summary,
        metrics=harvested.metrics,
        tags=task.tags,
        turns=task.turns,
        joey=joey,
    )
    pouch.write_run(pouch_dir, result, harvested.raw)

    return result


def start_manual(
    task: Task,
    harness: str,
    model: str,
    *,
    pouch_dir: Path,
    joey: bool = False,
    now: datetime | None = None,
) -> tuple[PendingRun, str]:
    """Start a manual run: mint an id, write `pending.json`, return setup instructions.

    Asks the adapter for harness-specific setup instructions but never invokes
    the harness — a human drives the session by hand (see ADR-0009). The run's
    driver is recorded as `human`. `interactive` tasks are accepted. `joey` marks
    the pending run as a throwaway trial. Returns the written `PendingRun` and the
    instructions to show the human.
    """
    adapter = require_adapter(harness)

    started = now or datetime.now(UTC)
    run_id = pouch.new_run_id(pouch_dir, task.id, harness, model=model, now=started)

    instructions = adapter.start(task, model)

    pending = PendingRun(
        run_id=run_id,
        task=task.id,
        harness=harness,
        model=model,
        driver="human",
        turns=task.turns,
        tags=task.tags,
        joey=joey,
        created_at=started,
    )
    pouch.write_pending(pouch_dir, pending)

    return pending, instructions


def harvest_manual(
    run_id: str,
    session_id: str,
    pouch_dir: Path,
    *,
    ask: Asker,
    joey: bool | None = None,
) -> Result:
    """Complete a pending manual run by harvesting its externally-supplied session.

    Loads the pending run, hands `session_id` to the adapter, runs the survey
    through the injected `ask` (manual runs carry a survey; see ADR-0009),
    assembles the Result (driver `human`, task/harness/model/turns/tags from the
    pending run), writes its run directory, and removes `pending.json`. An
    unknown or already-harvested run id raises `HarvestError` and writes nothing.
    `joey` overrides the throwaway flag on the result; left as `None`, the
    pending run's value carries through.
    """
    pending = pouch.read_pending(pouch_dir, run_id)
    adapter = require_adapter(pending.harness)

    harvested = adapter.harvest(session_id)
    survey = collect_survey(ask)

    result = Result(
        run_id=pending.run_id,
        task=pending.task,
        harness=pending.harness,
        model=pending.model,
        driver="human",
        started_at=harvested.started_at,
        finished_at=harvested.finished_at,
        session_status=harvested.session_status,
        summary=harvested.summary,
        metrics=harvested.metrics,
        tags=pending.tags,
        turns=pending.turns,
        joey=pending.joey if joey is None else joey,
        survey=survey,
    )
    pouch.write_run(pouch_dir, result, harvested.raw)
    pouch.remove_pending(pouch_dir, run_id)

    return result
