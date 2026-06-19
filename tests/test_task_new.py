"""End-to-end tests of the `task new` scaffold command."""

import tomllib
from typing import TYPE_CHECKING

import pytest

from koalaty.exceptions import TaskScaffoldError

if TYPE_CHECKING:
    from pathlib import Path

    from cyclopts import App


def test_new_writes_full_layout(app: App, tmp_path: Path) -> None:
    """`task new` scaffolds every documented file and empty directory."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "quokka", "--tasks", str(tasks)])

    task_dir = tasks / "quokka"
    assert (task_dir / "task.toml").is_file()
    assert (task_dir / "prompt.md").read_text(encoding="utf-8").strip()
    assert (task_dir / "done.md").read_text(encoding="utf-8").strip()
    assert (task_dir / "rubric.md").read_text(encoding="utf-8").strip()
    assert (task_dir / "gum").is_dir()
    assert (task_dir / "tests").is_dir()


def test_new_toml_is_valid_and_documented(app: App, tmp_path: Path) -> None:
    """The scaffolded task.toml parses to the documented defaults and has comments."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "quokka", "--tasks", str(tasks)])

    text = (tasks / "quokka" / "task.toml").read_text(encoding="utf-8")
    config = tomllib.loads(text)
    assert config["turns"] == "one-shot"
    assert config["tags"] == []
    assert config["gum"] == {"type": "inline"}

    assert "# turns:" in text
    assert "# tags:" in text
    assert "# [gum]:" in text


def test_scaffold_round_trips_through_run_and_compare(
    app: App,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A freshly scaffolded task runs unedited and shows up in compare."""
    tasks = tmp_path / "tasks"
    pouch = tmp_path / "pouch"
    app(["task", "new", "quokka", "--tasks", str(tasks)])

    run_id = app(
        [
            "run",
            "quokka",
            "--harness",
            "fake",
            "--model",
            "opus48",
            "--pouch",
            str(pouch),
            "--tasks",
            str(tasks),
        ],
    )
    assert (pouch / run_id / "result.json").is_file()

    capsys.readouterr()
    app(["compare", "--pouch", str(pouch)])
    assert "quokka" in capsys.readouterr().out


def test_new_refuses_to_overwrite_existing_task(app: App, tmp_path: Path) -> None:
    """A colliding task directory fails clearly and is left untouched."""
    tasks = tmp_path / "tasks"
    existing = tasks / "quokka"
    existing.mkdir(parents=True)
    (existing / "prompt.md").write_text("hand-written", encoding="utf-8")

    with pytest.raises(TaskScaffoldError, match="already exists"):
        app(["task", "new", "quokka", "--tasks", str(tasks)])

    assert (existing / "prompt.md").read_text(encoding="utf-8") == "hand-written"
    assert list(existing.iterdir()) == [existing / "prompt.md"]


def test_new_rejects_invalid_id_without_writing(app: App, tmp_path: Path) -> None:
    """An id breaking the task-id pattern is rejected before anything is written."""
    tasks = tmp_path / "tasks"

    with pytest.raises(TaskScaffoldError, match="Bad_Id"):
        app(["task", "new", "Bad_Id", "--tasks", str(tasks)])

    assert not tasks.exists() or list(tasks.iterdir()) == []
