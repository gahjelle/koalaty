"""CLI definition and the thin run/compare orchestration.

The CLI layer stays thin: validation and the run-assembly orchestrator live
here, but all real logic lives in the domain modules they call.

TODO: Extract domain logic (interactive rejection, run assembly) out of this
module into domain functions so the CLI stays a pure thin wrapper.  Also
consider introducing a `koalaty.schemas` package to own shared domain types
(`Turns`, `Task`, `Result`, etc.) so domain modules don't reach into each
other for types — both `tasks.py` and `result.py` would depend on schemas
instead of each other.
"""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from koalaty import pouch
from koalaty.adapters import get_adapter, known_harnesses
from koalaty.adapters.base import InvocableAdapter
from koalaty.compare import build_grid, render_grid
from koalaty.config import DEFAULT_POUCH, DEFAULT_TASKS, POUCH_ENV, derive_driver
from koalaty.result import Result
from koalaty.tasks import Turns, load_task

_MODEL_PATTERN = re.compile(r"^[a-z0-9]+$")

PouchOption = Annotated[
    Path,
    Parameter(name="--pouch", help="Pouch directory (results store)."),
]

TasksOption = Annotated[
    Path,
    Parameter(name="--tasks", help="Tasks directory (task bundles)."),
]


def _validate_model(_type: type, value: str) -> None:
    """Reject model names that are not dash-free canonical slugs."""
    if not _MODEL_PATTERN.fullmatch(value):
        pattern = _MODEL_PATTERN.pattern
        msg = f"model {value!r} must match {pattern} (a-z, 0-9; no dashes)"
        raise ValueError(msg)


def _validate_harness(_type: type, value: str) -> None:
    """Reject harnesses without a registered adapter."""
    if value not in known_harnesses():
        known = ", ".join(known_harnesses())
        msg = f"unknown harness {value!r}; registered harnesses: {known}"
        raise ValueError(msg)


def run(
    task: str,
    *,
    harness: Annotated[str, Parameter(validator=_validate_harness)],
    model: Annotated[str, Parameter(validator=_validate_model)],
    pouch_dir: PouchOption = DEFAULT_POUCH,
    tasks_dir: TasksOption = DEFAULT_TASKS,
) -> str:
    """Run a task on a model in a harness and store the result in the pouch.

    Loads the task from disk, invokes the harness, harvests the session,
    assembles the result, and writes its run directory. An interactive task is
    rejected (manual-only); nothing is written on any rejection. Returns and
    prints the new run id.
    """
    loaded = load_task(tasks_dir, task)

    adapter = get_adapter(harness)
    if adapter is None:  # pragma: no cover - guarded by _validate_harness
        msg = f"unknown harness {harness!r}"
        raise ValueError(msg)

    if not isinstance(adapter, InvocableAdapter):
        msg = f"harness {harness!r} does not support headless invocation"
        raise TypeError(msg)

    if loaded.turns is Turns.interactive:
        msg = (
            f"task {task!r} is interactive (manual-only); drive it yourself and "
            f"use `start`/`harvest` instead of `run`"
        )
        raise ValueError(msg)

    driver = derive_driver(can_invoke=True, interactive=False)

    started = datetime.now(UTC)
    run_id = pouch.new_run_id(pouch_dir, task, harness, model, started)

    session_id = adapter.invoke(loaded, model)
    harvested = adapter.harvest(session_id)

    result = Result(
        run_id=run_id,
        task=task,
        harness=harness,
        model=model,
        driver=driver,
        started_at=harvested.started_at,
        finished_at=harvested.finished_at,
        outcome=harvested.outcome,
        summary=harvested.summary,
        tags=loaded.tags,
        turns=loaded.turns,
    )
    pouch.write_run(pouch_dir, result, harvested.raw)

    return run_id


def compare(
    task: str | None = None,
    *,
    pouch_dir: PouchOption = DEFAULT_POUCH,
) -> None:
    """Print a (model x harness) grid per task of the results in the pouch."""
    console = Console()
    results = pouch.read_results(pouch_dir)
    if not results:
        console.print(f"no runs found in {pouch_dir}")
        return

    tasks = [task] if task is not None else sorted({result.task for result in results})
    for task_id in tasks:
        console.print(render_grid(build_grid(results, task_id)))


def build_app() -> App:
    """Build the cyclopts application with the run and compare commands."""
    app = App(
        name="koalaty",
        help="Evaluate and compare models inside agent harnesses.",
        config=POUCH_ENV,
    )
    app.command(run)
    app.command(compare)
    return app
