"""The pouch: run-id minting and run-directory read/write.

The pouch is a directory of plain files, one subdirectory per run, and the
source of truth. `result.json` is authoritative; the run-id directory name is
only a label and is never parsed for information (ADR-0003).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from koalaty.config import config
from koalaty.exceptions import HarvestError
from koalaty.schemas.pending import PendingRun
from koalaty.schemas.result import Result

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

__all__ = [
    "mint_run_id",
    "new_run_id",
    "read_pending",
    "read_results",
    "remove_pending",
    "write_pending",
    "write_run",
]

RESULT_FILE = config.result.result_file
RAW_SESSION_FILE = config.result.raw_session_file
PENDING_FILE = config.result.pending_file


def default_shortid() -> str:
    """Return a fresh short id of the configured hex length."""
    return uuid4().hex[: config.run_id.shortid_length]


def mint_run_id(
    task: str,
    harness: str,
    model: str,
    *,
    now: datetime,
    is_taken: Callable[[str], bool],
    new_shortid: Callable[[], str] = default_shortid,
) -> str:
    """Mint a run id `<task>-<harness>-<model>-<YYYYMMDD>-<shortid>`.

    `now` is the UTC run-start instant. The shortid is regenerated while
    `is_taken` reports a collision, so the returned id names a free directory.
    """
    date = now.strftime(config.run_id.date_format)
    while True:
        run_id = f"{task}-{harness}-{model}-{date}-{new_shortid()}"
        if not is_taken(run_id):
            return run_id


def new_run_id(
    pouch: Path, task: str, harness: str, *, model: str, now: datetime
) -> str:
    """Mint a run id whose directory does not yet exist under `pouch`."""
    return mint_run_id(
        task,
        harness,
        model,
        now=now,
        is_taken=lambda run_id: (pouch / run_id).exists(),
    )


def write_run(pouch: Path, result: Result, raw: dict[str, Any]) -> Path:
    """Write `result.json` and `raw/session.json` for `result`'s run dir.

    Creates the pouch and run directory (`parents=True`). Returns the run dir.
    """
    run_dir = pouch / result.run_id
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / RESULT_FILE).write_text(
        result.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (run_dir / RAW_SESSION_FILE).write_text(
        json.dumps(raw, indent=2) + "\n", encoding="utf-8"
    )
    return run_dir


def write_pending(pouch: Path, pending: PendingRun) -> Path:
    """Write `pending.json` for `pending`'s run dir, creating it. Returns the dir.

    A pending run carries no `result.json`, so `read_results` (and thus
    `compare`) ignores it until `harvest` completes it (ADR-0008).
    """
    run_dir = pouch / pending.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / PENDING_FILE).write_text(
        pending.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    return run_dir


def read_pending(pouch: Path, run_id: str) -> PendingRun:
    """Load the `pending.json` for `run_id`, or raise if there is none.

    An absent `pending.json` means an unknown or already-harvested run; the
    caller must write nothing in that case (ADR-0008).
    """
    path = pouch / run_id / PENDING_FILE
    if not path.is_file():
        msg = f"no pending run {run_id!r} to harvest"
        raise HarvestError(msg)
    return PendingRun.model_validate_json(path.read_text(encoding="utf-8"))


def remove_pending(pouch: Path, run_id: str) -> None:
    """Remove the `pending.json` for `run_id`; harvest has completed the run."""
    (pouch / run_id / PENDING_FILE).unlink()


def read_results(pouch: Path) -> list[Result]:
    """Load every `result.json` under `pouch` (empty if the pouch is absent)."""
    if not pouch.exists():
        return []
    paths: Iterable[Path] = sorted(pouch.glob(f"*/{RESULT_FILE}"))
    return [
        Result.model_validate_json(path.read_text(encoding="utf-8")) for path in paths
    ]
