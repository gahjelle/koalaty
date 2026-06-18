"""End-to-end tests of the `run` command driving the fake adapter."""

import json
import re
from typing import TYPE_CHECKING

import cyclopts
import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from cyclopts import App

RUN_ID_RE = re.compile(r"^quokka-fake-opus48-\d{8}-[0-9a-f]{6}$")


def run_args(
    pouch: Path,
    *,
    task: str = "quokka",
    harness: str = "fake",
    model: str = "opus48",
) -> list[str]:
    """Build the argv for a `run` invocation against `pouch`."""
    return [
        "run",
        task,
        "--harness",
        harness,
        "--model",
        model,
        "--pouch",
        str(pouch),
    ]


def test_run_writes_result_and_raw_session(app: App, tmp_path: Path) -> None:
    """A run writes result.json with the right fields plus raw/session.json."""
    run_id = app(run_args(tmp_path))

    run_dir = tmp_path / run_id
    result = json.loads((run_dir / "result.json").read_text())
    assert result["schema_version"] == 1
    assert result["run_id"] == run_id
    assert result["task"] == "quokka"
    assert result["harness"] == "fake"
    assert result["model"] == "opus48"
    assert result["driver"] == "koalaty"
    assert result["outcome"] == "success"
    assert result["summary"]
    assert (run_dir / "raw" / "session.json").exists()


def test_run_id_follows_canonical_format(app: App, tmp_path: Path) -> None:
    """The run id matches `quokka-fake-opus48-<YYYYMMDD>-<6hex>`."""
    run_id = app(run_args(tmp_path))
    assert RUN_ID_RE.fullmatch(run_id)


def test_two_runs_coexist_with_distinct_ids(app: App, tmp_path: Path) -> None:
    """Running twice yields two coexisting run dirs with distinct ids."""
    first = app(run_args(tmp_path))
    second = app(run_args(tmp_path))

    assert first != second
    assert (tmp_path / first).is_dir()
    assert (tmp_path / second).is_dir()
    assert len(list(tmp_path.iterdir())) == 2


def test_run_rejects_non_canonical_model(app: App, tmp_path: Path) -> None:
    """A dashed model name is rejected before anything is written."""
    with pytest.raises(cyclopts.ValidationError):
        app(run_args(tmp_path, model="opus-4.8"))
    assert not list(tmp_path.iterdir())


def test_run_rejects_unknown_harness(app: App, tmp_path: Path) -> None:
    """An unregistered harness is rejected with a friendly error."""
    with pytest.raises(cyclopts.ValidationError):
        app(run_args(tmp_path, harness="claudecode"))
    assert not list(tmp_path.iterdir())


def test_run_rejects_unknown_task(app: App, tmp_path: Path) -> None:
    """A task id that is not bundled is rejected."""
    with pytest.raises(cyclopts.ValidationError):
        app(run_args(tmp_path, task="wombat"))
    assert not list(tmp_path.iterdir())


def test_pouch_env_var_overrides_default(
    app: App,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KOALATY_POUCH is used when --pouch is omitted."""
    monkeypatch.setenv("KOALATY_POUCH", str(tmp_path))
    run_id = app(["run", "quokka", "--harness", "fake", "--model", "opus48"])
    assert (tmp_path / run_id / "result.json").exists()
