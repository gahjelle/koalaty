"""CLI commands for authoring task bundles: `task new` and `task examples`.

The tasks directory is read from `config.tasks` at call time (see ADR-0011)
rather than taken as a CLI flag.
"""

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter

from koalaty.config import config
from koalaty.console import stdout
from koalaty.examples import copy_example, list_examples
from koalaty.exceptions import TaskScaffoldError
from koalaty.scaffold import scaffold_task

__all__ = ["task_examples", "task_new"]


def task_new(
    task: str | None = None,
    *,
    from_example: Annotated[
        str | None,
        Parameter(name="--from-example", help="Copy a bundled example task by name."),
    ] = None,
) -> Path:
    """Create a new task directory, blank or copied from a bundled example.

    With `--from-example <name>`, copies that example into `config.tasks/<task>/`
    (defaulting the id to the example's name). Otherwise scaffolds a blank task
    under `config.tasks/<task>/`. Requires an id or `--from-example`. Fails
    without touching disk on a bad id, a collision, or an unknown example.
    """
    if from_example is not None:
        return copy_example(config.tasks, from_example, task)
    if task is None:
        msg = "task new needs an id or --from-example <name>"
        raise TaskScaffoldError(msg)
    return scaffold_task(config.tasks, task)


def task_examples() -> None:
    """List the bundled example tasks with each one's name and title."""
    for example in list_examples():
        description = (
            f" \N{EM DASH} {example.description}" if example.description else ""
        )
        stdout.print(f"{example.id}  {example.title}{description}")
