"""Task schemas: the shape of a loaded task bundle and its sub-types."""

import re
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, field_validator

from koalaty.schemas import FrozenModel

__all__ = ["GitGum", "Gum", "InlineGum", "Task", "TaskConfig", "Turns"]

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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
    def full_sha(cls, value: str) -> str:
        """Reject any commit that is not a full 40-char hex SHA."""
        if not FULL_SHA_RE.fullmatch(value):
            msg = f"git gum commit {value!r} must be a full 40-char hex SHA"
            raise ValueError(msg)
        return value


Gum = Annotated[InlineGum | GitGum, Field(discriminator="type")]


class TaskConfig(FrozenModel):
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
