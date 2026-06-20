"""End-to-end tests of the manual feed `start` and `harvest` CLI commands."""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.adapters.fake import FAKE_SESSION_ID

if TYPE_CHECKING:
    from cyclopts import App
    from tests.conftest import TaskWriter

RUN_ID_RE = re.compile(r"^quokka-fake-opus48-\d{8}-[0-9a-f]{6}$")


def start_args(
    *,
    task: str = "quokka",
    harness: str = "fake",
    model: str = "opus48",
) -> list[str]:
    """Build the argv for a `start` invocation (pouch/tasks come from `config`)."""
    return ["start", task, "--harness", harness, "--model", model]


def test_start_writes_pending_and_returns_run_id(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Start mints a run id, writes pending.json, and prints instructions on stderr."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(start_args())

    assert RUN_ID_RE.fullmatch(run_id)
    run_dir = pouch / run_id
    pending = json.loads((run_dir / "pending.json").read_text())
    assert pending["run_id"] == run_id
    assert pending["driver"] == "human"
    assert not (run_dir / "result.json").exists()

    captured = capsys.readouterr()
    assert "harvest" in captured.err


def test_start_accepts_interactive_task(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """An interactive task is accepted by start (manual-only) and goes pending."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka", turns="interactive")
    run_id = app(start_args())

    pending = json.loads((pouch / run_id / "pending.json").read_text())
    assert pending["turns"] == "interactive"


def test_pending_run_is_ignored_by_compare(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A pending run lives in the pouch but compare reports no runs."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(start_args())
    assert (pouch / run_id).is_dir()

    app(["compare"])
    captured = capsys.readouterr()
    assert "no runs found" in captured.err


def test_harvest_completes_pending_run(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """Harvest turns a pending run into a result.json and removes pending.json."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(start_args())

    harvested = app(["harvest", run_id, "--session", FAKE_SESSION_ID])

    assert harvested == run_id
    run_dir = pouch / run_id
    result = json.loads((run_dir / "result.json").read_text())
    assert result["driver"] == "human"
    assert result["outcome"] == "success"
    assert (run_dir / "raw" / "session.json").exists()
    assert not (run_dir / "pending.json").exists()


def test_harvested_run_shows_up_in_compare(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Once harvested, the manual run is comparable like any other result."""
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(start_args())
    app(["harvest", run_id, "--session", FAKE_SESSION_ID])

    app(["compare"])
    captured = capsys.readouterr()
    assert "quokka" in captured.out


def test_harvest_rejects_unknown_run_id(
    app: App,
    tmp_path: Path,
) -> None:
    """Harvesting an unknown run id fails and writes nothing."""
    pouch = tmp_path / "pouch"
    with pytest.raises(Exception, match="wombat-fake-opus48-x"):
        app(["harvest", "wombat-fake-opus48-x", "--session", "s"])
    assert not pouch.exists() or not list(pouch.iterdir())
