"""Tests for the run_automated domain function."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.exceptions import HarvestError
from koalaty.runs import harvest_run, run_automated, start_run
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


def test_start_run_writes_pending_and_returns_it(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """start_run mints a run id, writes pending.json, and returns it plus setup text."""
    pouch = tmp_path / "pouch"
    tasks_dir = make_task(tmp_path / "tasks", "quokka")
    task = load_task(tasks_dir, "quokka")

    now = datetime(2026, 6, 18, 14, 0, 0, tzinfo=UTC)
    pending, instructions = start_run(task, "fake", "opus48", pouch, now=now)

    assert pending.task == "quokka"
    assert pending.harness == "fake"
    assert pending.model == "opus48"
    assert pending.driver == "human"
    assert pending.turns == "one-shot"
    assert pending.tags == []
    assert pending.run_id.startswith("quokka-fake-opus48-")
    assert instructions

    run_dir = pouch / pending.run_id
    stored = json.loads((run_dir / "pending.json").read_text())
    assert stored["run_id"] == pending.run_id
    assert not (run_dir / "result.json").exists()


def test_harvest_run_completes_pending_into_result(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """harvest_run writes result.json (driver=human) and removes pending.json."""
    pouch = tmp_path / "pouch"
    tasks_dir = make_task(tmp_path / "tasks", "quokka", tags=["drop-bear"])
    task = load_task(tasks_dir, "quokka")

    pending, _ = start_run(task, "fake", "opus48", pouch)
    result = harvest_run(pending.run_id, "session-xyz", pouch)

    assert result.run_id == pending.run_id
    assert result.task == "quokka"
    assert result.harness == "fake"
    assert result.model == "opus48"
    assert result.driver == "human"
    assert result.outcome == Outcome.success
    assert result.turns == "one-shot"
    assert result.tags == ["drop-bear"]

    run_dir = pouch / pending.run_id
    assert json.loads((run_dir / "result.json").read_text())["driver"] == "human"
    assert (run_dir / "raw" / "session.json").exists()
    assert not (run_dir / "pending.json").exists()


def test_harvest_run_rejects_unknown_run_id(tmp_path: Path) -> None:
    """Harvesting an unknown run id errors and writes nothing."""
    pouch = tmp_path / "pouch"

    with pytest.raises(HarvestError, match="quokka-fake-opus48-x"):
        harvest_run("quokka-fake-opus48-x", "session-xyz", pouch)

    assert not pouch.exists() or not list(pouch.iterdir())


def test_harvest_run_rejects_already_harvested_run(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """Re-harvesting a completed run errors; the first result is untouched."""
    pouch = tmp_path / "pouch"
    tasks_dir = make_task(tmp_path / "tasks", "quokka")
    task = load_task(tasks_dir, "quokka")

    pending, _ = start_run(task, "fake", "opus48", pouch)
    harvest_run(pending.run_id, "session-xyz", pouch)

    with pytest.raises(HarvestError, match=pending.run_id):
        harvest_run(pending.run_id, "session-xyz", pouch)
