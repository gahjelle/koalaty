"""End-to-end tests of the `run` command driving the fake adapter."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from cyclopts import App
    from tests.conftest import TaskWriter

RUN_ID_RE = re.compile(r"^quokka-fake-opus48-\d{8}-[0-9a-f]{6}$")


def run_args(
    pouch: Path,
    tasks: Path,
    *,
    task: str = "quokka",
    harness: str = "fake",
    model: str = "opus48",
) -> list[str]:
    """Build the argv for a `run` invocation against `pouch` and `tasks`."""
    return [
        "run",
        task,
        "--harness",
        harness,
        "--model",
        model,
        "--pouch",
        str(pouch),
        "--tasks",
        str(tasks),
    ]


def test_run_writes_result_and_raw_session(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A run loads a task from disk and writes result.json plus raw/session."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    run_id = app(run_args(pouch, tasks))

    run_dir = pouch / run_id
    result = json.loads((run_dir / "result.json").read_text())
    assert result["schema_version"] == 1
    assert result["run_id"] == run_id
    assert result["task"] == "quokka"
    assert result["harness"] == "fake"
    assert result["model"] == "opus48"
    assert result["driver"] == "koalaty"
    assert result["outcome"] == "success"
    assert result["summary"]
    assert result["tags"] == []
    assert result["turns"] == "one-shot"
    assert (run_dir / "raw" / "session.json").exists()


def test_run_session_uses_task_opening_prompt(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """The fake adapter builds its session from the loaded task's prompt."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka", prompt="Return 'quokka'.")
    run_id = app(run_args(pouch, tasks))

    raw = json.loads((pouch / run_id / "raw" / "session.json").read_text())
    assert raw["messages"][0]["content"] == "Return 'quokka'."


def test_run_records_task_tags(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A drop-bear tag on the task rides through to result.json."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka", tags=["drop-bear"])
    run_id = app(run_args(pouch, tasks))

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["tags"] == ["drop-bear"]


def test_run_records_scripted_turns(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A scripted task records `turns = "scripted"` on the result."""
    pouch = tmp_path / "pouch"
    tasks = make_task(
        tmp_path / "tasks",
        "quokka",
        turns="scripted",
        prompt="First turn.\n---\nSecond turn.",
    )
    run_id = app(run_args(pouch, tasks))

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["turns"] == "scripted"


def test_run_id_follows_canonical_format(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """The run id matches `quokka-fake-opus48-<YYYYMMDD>-<6hex>`."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    run_id = app(run_args(pouch, tasks))
    assert RUN_ID_RE.fullmatch(run_id)


def test_two_runs_coexist_with_distinct_ids(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """Running twice yields two coexisting run dirs with distinct ids."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    first = app(run_args(pouch, tasks))
    second = app(run_args(pouch, tasks))

    assert first != second
    assert (pouch / first).is_dir()
    assert (pouch / second).is_dir()
    assert len(list(pouch.iterdir())) == 2


def test_run_rejects_non_canonical_model(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A dashed model name is rejected before anything is written."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    with pytest.raises(Exception, match="opus"):
        app(run_args(pouch, tasks, model="opus-4.8"))
    assert not pouch.exists() or not list(pouch.iterdir())


def test_run_rejects_unknown_harness(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """An unregistered harness is rejected with a friendly error."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    with pytest.raises(Exception, match="claudecode"):
        app(run_args(pouch, tasks, harness="claudecode"))
    assert not pouch.exists() or not list(pouch.iterdir())


def test_run_rejects_missing_task_directory(
    app: App,
    tmp_path: Path,
) -> None:
    """A missing task directory fails clearly and writes nothing."""
    pouch = tmp_path / "pouch"
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    with pytest.raises(Exception, match="wombat"):
        app(run_args(pouch, tasks, task="wombat"))
    assert not pouch.exists() or not list(pouch.iterdir())


def test_run_rejects_missing_required_file(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A task missing prompt.md fails clearly and writes nothing."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    (tasks / "quokka" / "prompt.md").unlink()
    with pytest.raises(Exception, match=r"prompt\.md"):
        app(run_args(pouch, tasks))
    assert not pouch.exists() or not list(pouch.iterdir())


def test_run_rejects_interactive_task(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """An interactive task is rejected as manual-only and writes nothing."""
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka", turns="interactive")
    with pytest.raises(Exception, match="interactive"):
        app(run_args(pouch, tasks))
    assert not pouch.exists() or not list(pouch.iterdir())


def test_pouch_env_var_overrides_default(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """KOALATY_POUCH / KOALATY_TASKS steer a run when the options are omitted.

    configaroo resolves the env into `config` at import, so this runs the CLI in
    a fresh process (the env can't be injected after import) and checks that the
    result lands under the env-provided pouch.
    """
    pouch = tmp_path / "pouch"
    tasks = make_task(tmp_path / "tasks", "quokka")
    env = {
        **os.environ,
        "KOALATY_POUCH": str(pouch),
        "KOALATY_TASKS": str(tasks),
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "koalaty",
            "run",
            "quokka",
            "--harness",
            "fake",
            "--model",
            "opus48",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert list(pouch.glob("quokka-fake-opus48-*/result.json"))
