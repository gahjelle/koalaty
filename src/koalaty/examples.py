"""Bundled example tasks shipped as package data, plus copying them out.

Example tasks live under `koalaty/example_tasks/<name>/` inside the wheel. They
are copy-only (ADR-0004): `copy_example` copies one verbatim into the tasks
directory, after which it is an ordinary, user-owned task; `run` never resolves
an example in place. This module is the single bridge from package data to the
tasks directory.
"""

import importlib.resources
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from koalaty.exceptions import TaskScaffoldError
from koalaty.scaffold import validate_destination
from koalaty.tasks import load_task

if TYPE_CHECKING:
    from collections.abc import Iterator

    from koalaty.schemas.tasks import Task

__all__ = ["copy_example", "list_examples"]

EXAMPLES_PACKAGE = "koalaty"
EXAMPLES_DIR = "example_tasks"


@contextmanager
def examples_root() -> Iterator[Path]:
    """Yield the bundled example tasks directory as a real filesystem path."""
    resource = importlib.resources.files(EXAMPLES_PACKAGE) / EXAMPLES_DIR
    with importlib.resources.as_file(resource) as root:
        yield root


def example_names(root: Path) -> list[str]:
    """Return the sorted names of the bundled examples under `root`."""
    return sorted(entry.name for entry in root.iterdir() if entry.is_dir())


def list_examples() -> list[Task]:
    """Load every bundled example task for display (id, title, description)."""
    with examples_root() as root:
        return [load_task(root, name) for name in example_names(root)]


def copy_example(tasks_dir: Path, name: str, task_id: str | None = None) -> Path:
    """Copy the bundled example `name` into `tasks_dir`, returning the new dir.

    The destination id defaults to `name`; pass `task_id` to copy into
    `tasks_dir/<task_id>/` instead. Obeys the same id-validation and collision
    rules as the blank scaffold, and fails — writing nothing — on an unknown
    example, listing the available ones.
    """
    dest_id = task_id or name
    destination = validate_destination(tasks_dir, dest_id)

    with examples_root() as root:
        source = root / name
        if not source.is_dir():
            available = ", ".join(example_names(root))
            msg = f"unknown example {name!r}; available examples: {available}"
            raise TaskScaffoldError(msg)
        shutil.copytree(source, destination)
    return destination
