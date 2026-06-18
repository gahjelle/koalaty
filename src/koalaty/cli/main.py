"""CLI definition and the thin run/compare orchestration.

The CLI layer stays thin: validation and the run-assembly orchestrator live
here, but all real logic lives in the domain modules they call.
"""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter
from rich.console import Console

from koalaty import pouch
from koalaty.adapters import get_adapter, known_harnesses
from koalaty.compare import build_grid, render_grid
from koalaty.config import DEFAULT_POUCH, POUCH_ENV, derive_driver
from koalaty.result import Result
from koalaty.tasks import BUNDLED_TASKS, is_known_task

_MODEL_PATTERN = re.compile(r"^[a-z0-9]+$")

PouchOption = Annotated[
    Path,
    Parameter(name="--pouch", help="Pouch directory (results store)."),
]


def _validate_model(_type: type, value: str) -> None:
    """Reject model names that are not dash-free canonical slugs."""
    if not _MODEL_PATTERN.fullmatch(value):
        pattern = _MODEL_PATTERN.pattern
        msg = f"model {value!r} must match {pattern} (a-z, 0-9; no dashes)"
        raise ValueError(msg)


def _validate_task(_type: type, value: str) -> None:
    """Reject task ids that are not bundled."""
    if not is_known_task(value):
        known = ", ".join(sorted(BUNDLED_TASKS))
        msg = f"unknown task {value!r}; bundled tasks: {known}"
        raise ValueError(msg)


def _validate_harness(_type: type, value: str) -> None:
    """Reject harnesses without a registered adapter."""
    if value not in known_harnesses():
        known = ", ".join(known_harnesses())
        msg = f"unknown harness {value!r}; registered harnesses: {known}"
        raise ValueError(msg)


def run(
    task: Annotated[str, Parameter(validator=_validate_task)],
    *,
    harness: Annotated[str, Parameter(validator=_validate_harness)],
    model: Annotated[str, Parameter(validator=_validate_model)],
    pouch_dir: PouchOption = DEFAULT_POUCH,
) -> str:
    """Run a task on a model in a harness and store the result in the pouch.

    Validates inputs, invokes the harness, harvests the session, assembles the
    result, and writes its run directory. Returns and prints the new run id.
    """
    adapter = get_adapter(harness)
    if adapter is None:  # pragma: no cover - guarded by _validate_harness
        msg = f"unknown harness {harness!r}"
        raise ValueError(msg)

    started = datetime.now(UTC)
    run_id = pouch.new_run_id(pouch_dir, task, harness, model, started)

    session_id = adapter.invoke(task, model)
    harvested = adapter.harvest(session_id)

    driver = derive_driver(can_invoke=hasattr(adapter, "invoke"), interactive=False)
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
