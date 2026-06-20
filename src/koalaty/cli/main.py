"""CLI definition and the thin run/compare orchestration.

The CLI layer stays thin: CLI-level input validation lives here, but all
domain logic lives in the modules it calls.
"""

import re
from pathlib import Path
from typing import Annotated

from configaroo import print_configuration
from cyclopts import App, Parameter

from koalaty import pouch
from koalaty.adapters import known_harnesses
from koalaty.compare import build_grid, render_grid
from koalaty.config import config
from koalaty.console import stderr, stdout
from koalaty.examples import copy_example, list_examples
from koalaty.exceptions import TaskScaffoldError
from koalaty.runs import harvest_manual, run_automated, start_manual
from koalaty.scaffold import scaffold_task
from koalaty.tasks import load_task

__all__ = [
    "build_app",
    "compare",
    "harvest",
    "run",
    "show_config",
    "start",
    "task_examples",
    "task_new",
]

MODEL_PATTERN = re.compile(config.model.name_pattern)

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
    pouch_dir: PouchOption = config.pouch,
    tasks_dir: TasksOption = config.tasks,
) -> str:
    """Run a task on a model in a harness and store the result in the pouch.

    Loads the task from disk, delegates to run_automated for the full
    pipeline, and returns the new run id.
    """
    loaded = load_task(tasks_dir, task)
    result = run_automated(loaded, harness, model, pouch_dir)
    return result.run_id


def start(
    task: str,
    *,
    harness: Annotated[str, Parameter(validator=validate_harness)],
    model: Annotated[str, Parameter(validator=validate_model)],
    pouch_dir: PouchOption = config.pouch,
    tasks_dir: TasksOption = config.tasks,
) -> str:
    """Start a manual run: write a pending run and print setup instructions.

    Loads the task, delegates to start_manual (which never invokes the harness),
    prints the harness-specific setup instructions to stderr, and returns the
    new run id on stdout.
    """
    loaded = load_task(tasks_dir, task)
    pending, instructions = start_manual(loaded, harness, model, pouch_dir)
    stderr.print(instructions)
    return pending.run_id


def harvest(
    run_id: str,
    *,
    session: str,
    pouch_dir: PouchOption = config.pouch,
) -> str:
    """Harvest a pending manual run's externally-supplied session into a result.

    Delegates to harvest_manual, which writes result.json and removes pending.json,
    then returns the completed run id. Errors if the run id is unknown or has
    already been harvested.
    """
    result = harvest_manual(run_id, session, pouch_dir)
    return result.run_id


def compare(
    task: str | None = None,
    *,
    pouch_dir: PouchOption = config.pouch,
) -> None:
    """Print a (task x model) grid per harness of the results in the pouch."""
    results = pouch.read_results(pouch_dir)
    if not results:
        stderr.print(f"no runs found in {pouch_dir}")
        return

    if task is not None:
        results = [result for result in results if result.task == task]
    harnesses = sorted({result.harness for result in results})
    for harness in harnesses:
        stdout.print(render_grid(build_grid(results, harness)))


def task_new(
    task: str | None = None,
    *,
    from_example: Annotated[
        str | None,
        Parameter(name="--from-example", help="Copy a bundled example task by name."),
    ] = None,
    tasks_dir: TasksOption = config.tasks,
) -> Path:
    """Create a new task directory, blank or copied from a bundled example.

    With `--from-example <name>`, copies that example into `tasks_dir/<task>/`
    (defaulting the id to the example's name). Otherwise scaffolds a blank task
    under `tasks_dir/<task>/`. Requires an id or `--from-example`. Fails without
    touching disk on a bad id, a collision, or an unknown example.
    """
    if from_example is not None:
        return copy_example(tasks_dir, from_example, task)
    if task is None:
        msg = "task new needs an id or --from-example <name>"
        raise TaskScaffoldError(msg)
    return scaffold_task(tasks_dir, task)


def task_examples() -> None:
    """List the bundled example tasks with each one's name and title."""
    for example in list_examples():
        description = (
            f" \N{EM DASH} {example.description}" if example.description else ""
        )
        stdout.print(f"{example.id}  {example.title}{description}")


def show_config(
    *,
    section: str | None = None,
) -> None:
    """Print the current configuration registry to the console."""
    print_configuration(config, section)


def build_app() -> App:
    """Build the cyclopts application with all registered commands."""
    app = App(
        name="koalaty",
        help="Evaluate and compare models inside agent harnesses.",
    )
    app.command(run)
    app.command(start)
    app.command(harvest)
    app.command(compare)
    app.command(show_config)

    task_app = App(name="task", help="Author and scaffold task bundles.")
    task_app.command(task_new, name="new")
    task_app.command(task_examples, name="examples")
    app.command(task_app)
    return app
