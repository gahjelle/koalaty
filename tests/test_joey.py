"""Joey flag across both feeds: throwaway runs marked on pending runs and results.

A joey is a throwaway trial run that should not count (CONTEXT.md). This slice
only records the flag on `PendingRun` and `Result`; excluding joeys from
`compare` is a later slice.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from koalaty.adapters.fake import FAKE_SESSION_ID

if TYPE_CHECKING:
    from cyclopts import App
    from tests.conftest import TaskWriter


def test_run_defaults_to_not_joey(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """Without the flag, a run is not a joey — the flag defaults to false."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(["run", "quokka", "--harness", "fake", "--model", "opus48"])

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["joey"] is False


def test_run_records_joey(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """`run --joey` marks the automated result as a throwaway."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(["run", "quokka", "--harness", "fake", "--model", "opus48", "--joey"])

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["joey"] is True


def test_harvest_joey_overrides_pending(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """`harvest --joey` sets joey on a result whose pending run was not a joey."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(["start", "quokka", "--harness", "fake", "--model", "opus48"])
    app(["harvest", run_id, "--session", FAKE_SESSION_ID, "--joey"])

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["joey"] is True


def test_harvest_no_joey_clears_pending(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """`harvest --no-joey` clears the flag a joey pending run carried."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(
        ["start", "quokka", "--harness", "fake", "--model", "opus48", "--joey"]
    )
    app(["harvest", run_id, "--session", FAKE_SESSION_ID, "--no-joey"])

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["joey"] is False


def test_start_records_joey_on_pending(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """`start --joey` marks the pending run as a throwaway, visible while pending."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(
        ["start", "quokka", "--harness", "fake", "--model", "opus48", "--joey"]
    )

    pending = json.loads((pouch / run_id / "pending.json").read_text())
    assert pending["joey"] is True


def test_start_joey_carries_through_harvest(
    app: App,
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A joey started run stays a joey after a plain harvest (no flag)."""
    pouch = tmp_path / "pouch"
    make_task(tmp_path / "tasks", "quokka")
    run_id = app(
        ["start", "quokka", "--harness", "fake", "--model", "opus48", "--joey"]
    )
    app(["harvest", run_id, "--session", FAKE_SESSION_ID])

    result = json.loads((pouch / run_id / "result.json").read_text())
    assert result["joey"] is True
