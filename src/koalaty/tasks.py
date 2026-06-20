"""Loading on-disk task bundles into validated `Task` objects.

A task lives in `tasks/<id>/` as plain files: `task.toml` (config) and
`prompt.md` (the prompt) are required; `done.md`, `gum/`, `tests/`, and
`rubric.md` are optional. This module is the read path — it parses and
validates a bundle but never checks out a fixture (see ADR-0004).
"""

import re
import tomllib
from pathlib import Path

from pydantic import ValidationError

from koalaty.config import config
from koalaty.exceptions import TaskLoadError
from koalaty.schemas.tasks import Task, TaskConfig, Turns

__all__ = ["load_task"]

TASK_ID_RE = re.compile(config.task.id_pattern)


def default_title(task_id: str) -> str:
    """Default a missing title from the id: dashes to spaces, titlecased."""
    return task_id.replace("-", " ").title()


def split_prompt(text: str, turns: Turns) -> list[str]:
    """Split `prompt.md` into the ordered turn list for `turns`.

    `scripted` splits on bare `---` lines and must yield at least two turns;
    every other turn structure keeps the whole file as one literal prompt.
    """
    if turns is not Turns.scripted:
        return [text.strip()]

    separator = config.task.turn_separator
    segments: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.rstrip() == separator:
            segments.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    segments.append("\n".join(current).strip())

    prompts = [segment for segment in segments if segment]
    if len(prompts) < config.task.min_scripted_turns:
        msg = (
            f"scripted prompt must split into at least two turns on bare "
            f"{separator!r} lines; found {len(prompts)}"
        )
        raise TaskLoadError(msg)
    return prompts


def read_optional(task_dir: Path, name: str) -> str | None:
    """Return the text of an optional task file, or None when it is absent."""
    path = task_dir / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def require(task_dir: Path, name: str) -> Path:
    """Return a required task file's path, raising a clear error if absent."""
    path = task_dir / name
    if not path.is_file():
        msg = f"task {task_dir.name!r} is missing required file {name}"
        raise TaskLoadError(msg)
    return path


def load_task(tasks_dir: Path, task_id: str) -> Task:
    """Load and validate `tasks_dir/<task_id>/` into a `Task`.

    Raises `TaskLoadError` for a bad id, a missing directory or required file,
    or any malformed `task.toml` / `prompt.md`.
    """
    if not TASK_ID_RE.fullmatch(task_id):
        msg = f"invalid task id {task_id!r}; must match {TASK_ID_RE.pattern}"
        raise TaskLoadError(msg)

    task_dir = tasks_dir / task_id
    if not task_dir.is_dir():
        msg = f"no task {task_id!r} found in {tasks_dir}"
        raise TaskLoadError(msg)

    task_file = config.task.task_file
    config_path = require(task_dir, task_file)
    prompt_path = require(task_dir, config.task.prompt_file)

    try:
        raw_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        msg = f"task {task_id!r} has invalid {task_file}: {error}"
        raise TaskLoadError(msg) from error

    try:
        task_config = TaskConfig.model_validate(raw_config)
    except ValidationError as error:
        msg = f"task {task_id!r} has invalid {task_file}: {error}"
        raise TaskLoadError(msg) from error

    prompts = split_prompt(prompt_path.read_text(encoding="utf-8"), task_config.turns)

    return Task(
        id=task_id,
        title=task_config.title or default_title(task_id),
        description=task_config.description,
        turns=task_config.turns,
        tags=task_config.tags,
        gum=task_config.gum,
        prompts=prompts,
        done=read_optional(task_dir, config.task.done_file),
        rubric=read_optional(task_dir, config.task.rubric_file),
    )
