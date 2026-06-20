"""Shared test fixtures."""

import textwrap
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty import survey
from koalaty.cli.main import build_app
from koalaty.config import config

if TYPE_CHECKING:
    from cyclopts import App

# A helper that writes a `tasks/<id>/` bundle on disk and returns its root.
TaskWriter = Callable[..., Path]


class StubAsker:
    """A non-interactive `Asker`: ratings answered in call order, fixed notes.

    The injected test seam for the survey (the analogue of the fake adapter),
    so harvest never blocks on real stdin. `collect_survey` asks the three
    ratings in friction → hand-holding → frustration order, so `ratings` maps
    to those fields positionally.
    """

    def __init__(self, ratings: list[int], notes: str) -> None:
        """Answer ratings from `ratings` (in order) and notes with `notes`."""
        self._ratings = iter(ratings)
        self._notes = notes

    def rating(self, prompt: str) -> int:  # noqa: ARG002 — prompt unused by the stub
        """Return the next canned rating."""
        return next(self._ratings)

    def text(self, prompt: str) -> str:  # noqa: ARG002 — prompt unused by the stub
        """Return the canned free-text notes."""
        return self._notes


@dataclass
class SurveyStub:
    """Configurable survey answers a test can tweak before harvesting."""

    ratings: list[int] = field(default_factory=lambda: [2, 3, 1])
    notes: str = "it was fine"


@pytest.fixture(autouse=True)
def survey_stub(monkeypatch: pytest.MonkeyPatch) -> SurveyStub:
    """Swap the interactive survey asker for a stub so harvest never blocks.

    Autouse so any CLI `harvest` stays hermetic; returns the answer holder so a
    test can set `survey_stub.ratings` / `.notes` to assert what gets stored.
    A fresh `StubAsker` per call keeps the rating iterator unexhausted.
    """
    stub = SurveyStub()
    monkeypatch.setattr(
        survey, "make_asker", lambda: StubAsker(stub.ratings, stub.notes)
    )
    return stub


@pytest.fixture
def asker() -> StubAsker:
    """Return a ready stub asker for tests that call `harvest_manual` directly."""
    return StubAsker(ratings=[2, 3, 1], notes="it was fine")


@pytest.fixture(autouse=True)
def isolate_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the config singleton's settings at this test's tmp_path.

    The CLI reads `config.tasks` / `config.pouch` (no `--tasks`/`--pouch` flags
    anymore), so monkeypatching the now-mutable `config` is how each test gets an
    isolated tasks dir and pouch. Autouse so every test is isolated by default.
    """
    monkeypatch.setattr(config, "tasks", tmp_path / "tasks")
    monkeypatch.setattr(config, "pouch", tmp_path / "pouch")


@pytest.fixture
def app() -> App:
    """Return a koalaty app wired for clean in-process invocation in tests.

    The autouse `isolate_config` fixture runs first (autouse fixtures precede
    explicitly-requested ones in the same scope), so the app is built *after*
    `config` is pointed at the test's tmp_path — the task validator reads
    `config.tasks` at parse time. `exit_on_error=False` lets
    validation errors raise instead of exiting, and `result_action="return_value"`
    returns the command's value (e.g. the run id).
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
        cfg = config.task
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
        (task_dir / cfg.task_file).write_text("\n".join(lines) + "\n", encoding="utf-8")

        (task_dir / cfg.prompt_file).write_text(prompt, encoding="utf-8")
        if done is not None:
            (task_dir / cfg.done_file).write_text(done, encoding="utf-8")
        if rubric is not None:
            (task_dir / cfg.rubric_file).write_text(rubric, encoding="utf-8")
        return tasks_root

    return _write
