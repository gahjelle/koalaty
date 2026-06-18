"""Loading on-disk task bundles into validated `Task` objects.

A task lives in `tasks/<id>/` as plain files: `task.toml` (config) and
`prompt.md` (the prompt) are required; `done.md`, `gum/`, `tests/`, and
`rubric.md` are optional. This module is the read path — it parses and
validates a bundle but never checks out a fixture (see ADR-0004).
"""

import re
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError, field_validator

from koalaty.models import FrozenModel

# A task id is lowercase/digits with internal single dashes; never parsed for
# meaning, only used to name the bundle directory.
_TASK_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# A git gum pins a full 40-char hex commit SHA; branches/tags/short SHAs are out.
_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
# A scripted prompt splits on lines that are exactly this separator.
_TURN_SEPARATOR = "---"
_MIN_SCRIPTED_TURNS = 2

_CONFIG_FILE = "task.toml"
_PROMPT_FILE = "prompt.md"
_DONE_FILE = "done.md"
_RUBRIC_FILE = "rubric.md"


class TaskError(Exception):
    """A task bundle is missing, malformed, or fails validation."""


class Turns(StrEnum):
    """A task's turn structure (see CONTEXT.md)."""

    one_shot = "one-shot"
    scripted = "scripted"
    interactive = "interactive"


class InlineGum(FrozenModel):
    """A gum whose fixture files live inline under the task's `gum/`."""

    type: Literal["inline"] = "inline"


class GitGum(FrozenModel):
    """A gum pinned to a git `url` at a full-40-hex `commit`."""

    type: Literal["git"]
    url: str
    commit: str

    @field_validator("commit")
    @classmethod
    def _full_sha(cls, value: str) -> str:
        """Reject any commit that is not a full 40-char hex SHA."""
        if not _FULL_SHA_RE.fullmatch(value):
            msg = f"git gum commit {value!r} must be a full 40-char hex SHA"
            raise ValueError(msg)
        return value


Gum = Annotated[InlineGum | GitGum, Field(discriminator="type")]


class _TaskConfig(FrozenModel):
    """The validated shape of a task's `task.toml`."""

    turns: Turns
    tags: list[str] = []  # noqa: RUF012 — pydantic deep-copies field defaults
    title: str | None = None
    description: str | None = None
    gum: Gum = InlineGum()


class Task(FrozenModel):
    """A loaded, validated task bundle.

    `prompts` is the ordered turn list: one literal prompt for `one-shot` /
    `interactive`, two or more for `scripted`. The adapter starts a session
    from `prompts[0]`, the opening prompt.
    """

    id: str
    title: str
    description: str | None
    turns: Turns
    tags: list[str]
    gum: Gum
    prompts: list[str]
    done: str | None
    rubric: str | None


def _default_title(task_id: str) -> str:
    """Default a missing title from the id: dashes to spaces, titlecased."""
    return task_id.replace("-", " ").title()


def _split_prompt(text: str, turns: Turns) -> list[str]:
    """Split `prompt.md` into the ordered turn list for `turns`.

    `scripted` splits on bare `---` lines and must yield at least two turns;
    every other turn structure keeps the whole file as one literal prompt.
    """
    if turns is not Turns.scripted:
        return [text.strip()]

    segments: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.rstrip() == _TURN_SEPARATOR:
            segments.append("\n".join(current).strip())
            current = []
        else:
            current.append(line)
    segments.append("\n".join(current).strip())

    prompts = [segment for segment in segments if segment]
    if len(prompts) < _MIN_SCRIPTED_TURNS:
        msg = (
            f"scripted prompt must split into at least two turns on bare "
            f"{_TURN_SEPARATOR!r} lines; found {len(prompts)}"
        )
        raise TaskError(msg)
    return prompts


def _read_optional(task_dir: Path, name: str) -> str | None:
    """Return the text of an optional task file, or None when it is absent."""
    path = task_dir / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def _require(task_dir: Path, name: str) -> Path:
    """Return a required task file's path, raising a clear error if absent."""
    path = task_dir / name
    if not path.is_file():
        msg = f"task {task_dir.name!r} is missing required file {name}"
        raise TaskError(msg)
    return path


def load_task(tasks_dir: Path, task_id: str) -> Task:
    """Load and validate `tasks_dir/<task_id>/` into a `Task`.

    Raises `TaskError` for a bad id, a missing directory or required file, or
    any malformed `task.toml` / `prompt.md`.
    """
    if not _TASK_ID_RE.fullmatch(task_id):
        msg = f"invalid task id {task_id!r}; must match {_TASK_ID_RE.pattern}"
        raise TaskError(msg)

    task_dir = tasks_dir / task_id
    if not task_dir.is_dir():
        msg = f"no task {task_id!r} found in {tasks_dir}"
        raise TaskError(msg)

    config_path = _require(task_dir, _CONFIG_FILE)
    prompt_path = _require(task_dir, _PROMPT_FILE)

    try:
        raw_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        msg = f"task {task_id!r} has invalid {_CONFIG_FILE}: {error}"
        raise TaskError(msg) from error

    try:
        config = _TaskConfig.model_validate(raw_config)
    except ValidationError as error:
        msg = f"task {task_id!r} has invalid {_CONFIG_FILE}: {error}"
        raise TaskError(msg) from error

    prompts = _split_prompt(prompt_path.read_text(encoding="utf-8"), config.turns)

    return Task(
        id=task_id,
        title=config.title or _default_title(task_id),
        description=config.description,
        turns=config.turns,
        tags=config.tags,
        gum=config.gum,
        prompts=prompts,
        done=_read_optional(task_dir, _DONE_FILE),
        rubric=_read_optional(task_dir, _RUBRIC_FILE),
    )
