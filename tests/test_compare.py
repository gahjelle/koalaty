"""Tests for the comparison grid and the ``compare`` command."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from koalaty.compare import Tally, build_grid
from koalaty.result import Outcome, Result

if TYPE_CHECKING:
    from pathlib import Path

    from cyclopts import App

_TS = datetime(2026, 1, 1, tzinfo=UTC)


def _result(model: str, harness: str, outcome: Outcome, task: str = "quokka") -> Result:
    """Build a minimal result for grid tests."""
    return Result(
        run_id=f"{task}-{harness}-{model}-20260101-aaaaaa",
        task=task,
        harness=harness,
        model=model,
        driver="koalaty",
        started_at=_TS,
        finished_at=_TS,
        outcome=outcome,
        summary="s",
    )


def test_build_grid_tallies_per_model_harness() -> None:
    """build_grid tallies per (model, harness), filtered to the given task."""
    results = [
        _result("opus48", "fake", Outcome.success),
        _result("opus48", "fake", Outcome.failure),
        _result("sonnet46", "fake", Outcome.success),
        _result("opus48", "fake", Outcome.success, task="wombat"),
    ]
    grid = build_grid(results, "quokka")

    assert grid.task == "quokka"
    assert grid.tallies[("opus48", "fake")] == Tally(success=1, failure=1)
    assert grid.tallies[("sonnet46", "fake")] == Tally(success=1, failure=0)
    assert ("opus48", "fake") in grid.tallies
    assert grid.models == ["opus48", "sonnet46"]
    assert grid.harnesses == ["fake"]


def test_compare_prints_grid(app: App, tmp_path: Path, capsys) -> None:  # noqa: ANN001
    """Compare prints a grid titled with the task for runs in the pouch."""
    pouch = str(tmp_path)
    app(["run", "quokka", "--harness", "fake", "--model", "opus48", "--pouch", pouch])
    capsys.readouterr()

    app(["compare", "--pouch", str(tmp_path)])
    out = capsys.readouterr().out
    assert "quokka" in out
    assert "opus48" in out
    assert "fake" in out


def test_compare_friendly_when_empty(app: App, tmp_path: Path, capsys) -> None:  # noqa: ANN001
    """Compare reports a friendly message when the pouch has no runs."""
    app(["compare", "--pouch", str(tmp_path)])
    out = capsys.readouterr().out
    assert "no runs found" in out
    assert str(tmp_path) in out
