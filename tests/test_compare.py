"""Tests for the comparison grid and the `compare` command."""

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from koalaty.compare import Tally, build_grid, render_grid
from koalaty.schemas.result import Result, SessionStatus
from koalaty.schemas.tasks import Turns

if TYPE_CHECKING:
    import pytest
    from cyclopts import App
    from tests.conftest import TaskWriter

_TS = datetime(2026, 1, 1, tzinfo=UTC)


def _result(
    model: str, harness: str, status: SessionStatus, *, task: str = "quokka"
) -> Result:
    """Build a minimal result for grid tests."""
    return Result(
        run_id=f"{task}-{harness}-{model}-20260101-aaaaaa",
        task=task,
        harness=harness,
        model=model,
        driver="koalaty",
        started_at=_TS,
        finished_at=_TS,
        session_status=status,
        summary="s",
        tags=[],
        turns=Turns.one_shot,
    )


def test_build_grid_tallies_per_task_model() -> None:
    """build_grid tallies per (task, model), filtered to the given harness."""
    results = [
        _result("opus48", "fake", SessionStatus.completed),
        _result("opus48", "fake", SessionStatus.errored),
        _result("sonnet46", "fake", SessionStatus.completed),
        _result("opus48", "fake", SessionStatus.completed, task="wombat"),
        _result("opus48", "claudecode", SessionStatus.completed),
    ]
    grid = build_grid(results, "fake")

    assert grid.harness == "fake"
    assert grid.tallies[("quokka", "opus48")] == Tally(completed=1, incomplete=1)
    assert grid.tallies[("quokka", "sonnet46")] == Tally(completed=1, incomplete=0)
    assert grid.tallies[("wombat", "opus48")] == Tally(completed=1, incomplete=0)
    assert ("quokka", "opus48") in grid.tallies
    assert grid.tasks == ["quokka", "wombat"]
    assert grid.models == ["opus48", "sonnet46"]


def test_render_grid_is_titled_harness_with_model_columns() -> None:
    """render_grid titles the table with the harness, columns = models."""
    results = [
        _result("opus48", "fake", SessionStatus.completed, task="quokka"),
        _result("sonnet46", "fake", SessionStatus.errored, task="quokka"),
        _result("opus48", "fake", SessionStatus.completed, task="wombat"),
    ]
    table = render_grid(build_grid(results, "fake"))

    assert table.title == "fake"
    headers = [column.header for column in table.columns]
    assert headers == ["task", "opus48", "sonnet46"]


def test_render_grid_marks_empty_task_model_combos() -> None:
    """An absent (task, model) combo renders as the dim empty-cell glyph."""
    results = [
        _result("opus48", "fake", SessionStatus.completed, task="quokka"),
        _result("sonnet46", "fake", SessionStatus.completed, task="wombat"),
    ]
    table = render_grid(build_grid(results, "fake"))

    rendered = [[str(cell) for cell in column.cells] for column in table.columns]
    # Columns: [task, opus48, sonnet46]; wombat has no opus48 run.
    assert rendered[0] == ["quokka", "wombat"]
    assert "\N{EN DASH}" in rendered[1][1]
    assert "dim" in rendered[1][1]


def test_compare_prints_grid(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Compare prints a grid titled with the harness for runs in the pouch."""
    make_task(tmp_path / "tasks", "quokka")
    app(["run", "quokka", "--harness", "fake", "--model", "opus48"])
    capsys.readouterr()

    app(["compare"])
    out = capsys.readouterr().out
    assert "quokka" in out
    assert "opus48" in out
    assert "fake" in out


def test_compare_task_argument_narrows_rows(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The optional task argument narrows the harness tables to that task's row."""
    make_task(tmp_path / "tasks", "quokka")
    make_task(tmp_path / "tasks", "wombat")
    for task in ("quokka", "wombat"):
        app(["run", task, "--harness", "fake", "--model", "opus48"])
    capsys.readouterr()

    app(["compare", "wombat"])
    out = capsys.readouterr().out
    assert "wombat" in out
    assert "quokka" not in out


def test_compare_friendly_when_empty(
    app: App,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Compare reports a friendly message when the pouch has no runs."""
    app(["compare"])
    err = capsys.readouterr().err
    assert "no runs found" in err
    assert str(tmp_path) in err
