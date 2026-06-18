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

from koalaty.exceptions import TaskLoadError
from koalaty.schemas.tasks import Task, TaskConfig, Turns

__all__ = ["load_task"]

TASK_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TURN_SEPARATOR = "---"
MIN_SCRIPTED_TURNS = 2

CONFIG_FILE = "task.toml"
PROMPT_FILE = "prompt.md"
DONE_FILE = "done.md"
RUBRIC_FILE = "rubric.md"


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

    segments: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.rstrip() == TURN_SEPARATOR:
            segments.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    segments.append("\n".join(current).strip())

    prompts = [segment for segment in segments if segment]
    if len(prompts) < MIN_SCRIPTED_TURNS:
        msg = (
            f"scripted prompt must split into at least two turns on bare "
            f"{TURN_SEPARATOR!r} lines; found {len(prompts)}"
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

    config_path = require(task_dir, CONFIG_FILE)
    prompt_path = require(task_dir, PROMPT_FILE)

    try:
        raw_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        msg = f"task {task_id!r} has invalid {CONFIG_FILE}: {error}"
        raise TaskLoadError(msg) from error

    try:
        config = TaskConfig.model_validate(raw_config)
    except ValidationError as error:
        msg = f"task {task_id!r} has invalid {CONFIG_FILE}: {error}"
        raise TaskLoadError(msg) from error

    prompts = split_prompt(prompt_path.read_text(encoding="utf-8"), config.turns)

    return Task(
        id=task_id,
        title=config.title or default_title(task_id),
        description=config.description,
        turns=config.turns,
        tags=config.tags,
        gum=config.gum,
        prompts=prompts,
        done=read_optional(task_dir, DONE_FILE),
        rubric=read_optional(task_dir, RUBRIC_FILE),
    )
