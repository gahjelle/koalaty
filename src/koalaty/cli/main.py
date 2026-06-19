"""CLI definition and the thin run/compare orchestration.

The CLI layer stays thin: CLI-level input validation lives here, but all
domain logic lives in the modules it calls.
"""

import re
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from koalaty import pouch
from koalaty.adapters import known_harnesses
from koalaty.compare import build_grid, render_grid
from koalaty.config import DEFAULT_POUCH, DEFAULT_TASKS, POUCH_ENV
from koalaty.runs import run_automated
from koalaty.scaffold import scaffold_task
from koalaty.tasks import load_task

__all__ = ["build_app", "compare", "run", "task_new"]

MODEL_PATTERN = re.compile(r"^[a-z0-9]+$")

PouchOption = Annotated[
    Path,
    Parameter(name="--pouch", help="Pouch directory (results store)."),
]

TasksOption = Annotated[
    Path,
    Parameter(name="--tasks", help="Tasks directory (task bundles)."),
]


def validate_model(_type: type, value: str) -> None:
    """Reject model names that are not dash-free canonical slugs."""
    if not MODEL_PATTERN.fullmatch(value):
        pattern = MODEL_PATTERN.pattern
        msg = f"model {value!r} must match {pattern} (a-z, 0-9; no dashes)"
        raise ValueError(msg)


def validate_harness(_type: type, value: str) -> None:
    """Reject harnesses without a registered adapter."""
    if value not in known_harnesses():
        known = ", ".join(known_harnesses())
        msg = f"unknown harness {value!r}; registered harnesses: {known}"
        raise ValueError(msg)


def run(
    task: str,
    *,
    harness: Annotated[str, Parameter(validator=validate_harness)],
    model: Annotated[str, Parameter(validator=validate_model)],
    pouch_dir: PouchOption = DEFAULT_POUCH,
    tasks_dir: TasksOption = DEFAULT_TASKS,
) -> str:
    """Run a task on a model in a harness and store the result in the pouch.

    Loads the task from disk, delegates to run_automated for the full
    pipeline, and returns the new run id.
    """
    loaded = load_task(tasks_dir, task)
    result = run_automated(loaded, harness, model, pouch_dir)
    return result.run_id


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


def task_new(
    task_id: str,
    *,
    tasks_dir: TasksOption = DEFAULT_TASKS,
) -> Path:
    """Scaffold a new task directory that loads and runs unedited.

    Writes the full documented layout under `tasks_dir/<task_id>/` and returns
    the new directory. Fails without touching disk on a bad id or a collision.
    """
    return scaffold_task(tasks_dir, task_id)


def build_app() -> App:
    """Build the cyclopts application with the run, compare, and task commands."""
    app = App(
        name="koalaty",
        help="Evaluate and compare models inside agent harnesses.",
        config=POUCH_ENV,
    )
    app.command(run)
    app.command(compare)

    task_app = App(name="task", help="Author and scaffold task bundles.")
    task_app.command(task_new, name="new")
    app.command(task_app)
    return app
