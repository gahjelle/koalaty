"""Tests for the run_automated domain function."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.runs import run_automated
from koalaty.schemas.result import Outcome
from koalaty.tasks import load_task

if TYPE_CHECKING:
    from tests.conftest import TaskWriter


def test_run_automated_writes_result_and_returns_it(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """run_automated writes result.json + raw/session.json and returns the Result."""
    pouch = tmp_path / "pouch"
    tasks_dir = make_task(tmp_path / "tasks", "quokka")
    task = load_task(tasks_dir, "quokka")

    now = datetime(2026, 6, 18, 14, 0, 0, tzinfo=UTC)
    result = run_automated(task, "fake", "opus48", pouch, now=now)

    assert result.task == "quokka"
    assert result.harness == "fake"
    assert result.model == "opus48"
    assert result.driver == "koalaty"
    assert result.outcome == Outcome.success
    assert result.turns == "one-shot"
    assert result.tags == []
    assert result.run_id.startswith("quokka-fake-opus48-")

    run_dir = pouch / result.run_id
    stored = json.loads((run_dir / "result.json").read_text())
    assert stored["run_id"] == result.run_id
    assert (run_dir / "raw" / "session.json").exists()


def test_run_automated_rejects_unknown_harness(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """An unregistered harness is rejected with a ValueError."""
    pouch = tmp_path / "pouch"
    tasks_dir = make_task(tmp_path / "tasks", "quokka")
    task = load_task(tasks_dir, "quokka")

    with pytest.raises(ValueError, match="claudecode"):
        run_automated(task, "claudecode", "opus48", pouch)

    assert not pouch.exists() or not list(pouch.iterdir())


def test_run_automated_rejects_interactive_task(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """An interactive task is rejected as manual-only."""
    pouch = tmp_path / "pouch"
    tasks_dir = make_task(tmp_path / "tasks", "quokka", turns="interactive")
    task = load_task(tasks_dir, "quokka")

    with pytest.raises(ValueError, match="interactive"):
        run_automated(task, "fake", "opus48", pouch)

    assert not pouch.exists() or not list(pouch.iterdir())
