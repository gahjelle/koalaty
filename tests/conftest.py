"""Shared test fixtures."""

import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.cli.main import build_app

if TYPE_CHECKING:
    from cyclopts import App

# A helper that writes a `tasks/<id>/` bundle on disk and returns its root.
TaskWriter = Callable[..., Path]


@pytest.fixture
def app() -> App:
    """Return a koalaty app wired for clean in-process invocation in tests.

    `exit_on_error=False` lets validation errors raise instead of exiting, and
    `result_action="return_value"` returns the command's value (e.g. run id).
    """
    app = build_app()
    app.exit_on_error = False
    app.result_action = "return_value"
    return app


@pytest.fixture
def make_task() -> TaskWriter:
    """Return a helper that writes a `tasks/<id>/` bundle on disk.

    Only `turns` and `prompt` shape most tests; `gum` takes a raw TOML body for
    the `[gum]` table so error cases can author it directly.
    """

    def _write(  # noqa: PLR0913 — a task bundle has many optional parts
        tasks_root: Path,
        task_id: str,
        *,
        turns: str = "one-shot",
        prompt: str = "Write a function that returns 'quokka'.",
        tags: list[str] | None = None,
        title: str | None = None,
        description: str | None = None,
        gum: str | None = None,
        done: str | None = None,
        rubric: str | None = None,
    ) -> Path:
        task_dir = tasks_root / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        lines = [f'turns = "{turns}"']
        if tags is not None:
            rendered = ", ".join(f'"{tag}"' for tag in tags)
            lines.append(f"tags = [{rendered}]")
        if title is not None:
            lines.append(f'title = "{title}"')
        if description is not None:
            lines.append(f'description = "{description}"')
        if gum is not None:
            lines.append(textwrap.dedent(gum).strip())
        (task_dir / "task.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")

        (task_dir / "prompt.md").write_text(prompt, encoding="utf-8")
        if done is not None:
            (task_dir / "done.md").write_text(done, encoding="utf-8")
        if rubric is not None:
            (task_dir / "rubric.md").write_text(rubric, encoding="utf-8")
        return tasks_root

    return _write
