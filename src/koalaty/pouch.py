"""The pouch: run-id minting and run-directory read/write.

The pouch is a directory of plain files, one subdirectory per run, and the
source of truth. ``result.json`` is authoritative; the run-id directory name is
only a label and is never parsed for information (ADR-0003).
"""

from __future__ import annotations

import json
from datetime import datetime  # noqa: TC003  (used at runtime by mint_run_id)
from pathlib import Path  # noqa: TC003  (used at runtime by the I/O helpers)
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from koalaty.result import Result

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

_RESULT_FILE = "result.json"
_RAW_SESSION_FILE = "raw/session.json"


def _default_shortid() -> str:
    """Return a fresh 6-hex-character short id."""
    return uuid4().hex[:6]


def mint_run_id(  # noqa: PLR0913 — is_taken/new_shortid are injected test seams
    task: str,
    harness: str,
    model: str,
    *,
    now: datetime,
    is_taken: Callable[[str], bool],
    new_shortid: Callable[[], str] = _default_shortid,
) -> str:
    """Mint a run id ``<task>-<harness>-<model>-<YYYYMMDD>-<shortid>``.

    ``now`` is the UTC run-start instant. The shortid is regenerated while
    ``is_taken`` reports a collision, so the returned id names a free directory.
    """
    date = now.strftime("%Y%m%d")
    while True:
        run_id = f"{task}-{harness}-{model}-{date}-{new_shortid()}"
        if not is_taken(run_id):
            return run_id


def new_run_id(pouch: Path, task: str, harness: str, model: str, now: datetime) -> str:
    """Mint a run id whose directory does not yet exist under ``pouch``."""
    return mint_run_id(
        task,
        harness,
        model,
        now=now,
        is_taken=lambda run_id: (pouch / run_id).exists(),
    )


def write_run(pouch: Path, result: Result, raw: dict[str, Any]) -> Path:
    """Write ``result.json`` and ``raw/session.json`` for ``result``'s run dir.

    Creates the pouch and run directory (``parents=True``). Returns the run dir.
    """
    run_dir = pouch / result.run_id
    (run_dir / "raw").mkdir(parents=True, exist_ok=True)
    (run_dir / _RESULT_FILE).write_text(
        result.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    (run_dir / _RAW_SESSION_FILE).write_text(
        json.dumps(raw, indent=2) + "\n", encoding="utf-8"
    )
    return run_dir


def read_results(pouch: Path) -> list[Result]:
    """Load every ``result.json`` under ``pouch`` (empty if the pouch is absent)."""
    if not pouch.exists():
        return []
    paths: Iterable[Path] = sorted(pouch.glob(f"*/{_RESULT_FILE}"))
    return [
        Result.model_validate_json(path.read_text(encoding="utf-8")) for path in paths
    ]
