"""Tests for early task-name validation via the dynamic `Literal`.

`run`/`start` get a `Literal` of the task ids found in `config.tasks` at
`build_app` time, so an unknown task is rejected up front. These build the app
*after* writing tasks (the `app` fixture builds too early for that), so the
`Literal` reflects the on-disk ids. The autouse `isolate_config` fixture points
`config.tasks`/`config.pouch` at this test's tmp_path.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.cli.main import build_app

if TYPE_CHECKING:
    from cyclopts import App
    from tests.conftest import TaskWriter


def _return_app() -> App:
    """Build an app that returns command values and raises instead of exiting."""
    app = build_app()
    app.exit_on_error = False
    app.result_action = "return_value"
    return app


def test_literal_choices_track_config_tasks(
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown task is rejected up front, listing the known ids as choices."""
    make_task(tmp_path / "tasks", "quokka")
    app = build_app()

    with pytest.raises(SystemExit):
        app.meta(["run", "wombat", "--harness", "fake", "--model", "opus48"])

    err = capsys.readouterr().err
    assert "wombat" in err
    assert "quokka" in err


def test_run_accepts_dashed_task_id(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A dashed id is a valid Literal choice (the reason it is Literal, not Enum)."""
    make_task(tmp_path / "tasks", "3d-render")
    app = _return_app()

    run_id = app(["run", "3d-render", "--harness", "fake", "--model", "opus48"])
    assert run_id.startswith("3d-render-fake-opus48-")


def test_empty_tasks_dir_falls_back_to_str(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty tasks dir falls back to `str`; the load-time error still boxes."""
    (tmp_path / "tasks").mkdir()
    app = build_app()

    with pytest.raises(SystemExit) as excinfo:
        app.meta(["run", "asdf", "--harness", "fake", "--model", "opus48"])

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "asdf" in err


def test_unknown_task_surfaced_even_without_harness(
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`run <bad-task>` surfaces the bad task even when --harness is omitted."""
    make_task(tmp_path / "tasks", "quokka")
    app = build_app()

    with pytest.raises(SystemExit):
        app.meta(["run", "asdf"])

    err = capsys.readouterr().err
    assert "asdf" in err
