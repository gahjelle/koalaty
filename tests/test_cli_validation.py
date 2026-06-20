"""Tests for early task-name validation via the `TaskParam` validator.

`run`/`start` annotate their `task` parameter with `TaskParam`, whose validator
checks `config.tasks` at parse time, so an unknown task is rejected up front
with a cyclopts error box. The autouse `isolate_config` fixture points
`config.tasks`/`config.pouch` at this test's tmp_path.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.cli.main import build_app

if TYPE_CHECKING:
    from tests.conftest import TaskWriter


def test_unknown_task_rejected_with_choices(
    tmp_path: Path,
    make_task: TaskWriter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown task is rejected up front, listing the known ids."""
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
    """A dashed id passes the validator (the reason it is a validator, not Enum)."""
    make_task(tmp_path / "tasks", "3d-render")
    app = build_app()
    app.exit_on_error = False
    app.result_action = "return_value"

    run_id = app(["run", "3d-render", "--harness", "fake", "--model", "opus48"])
    assert run_id.startswith("3d-render-fake-opus48-")


def test_empty_tasks_dir_rejects_any_task(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An empty tasks dir rejects any task name; the validator fires with no ids."""
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
