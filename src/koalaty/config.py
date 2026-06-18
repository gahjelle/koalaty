"""Configuration: pouch-location binding and driver derivation."""

from pathlib import Path

import cyclopts

__all__ = ["DEFAULT_POUCH", "DEFAULT_TASKS", "POUCH_ENV", "derive_driver"]

# Location precedence: `--pouch`/`--tasks` → `KOALATY_*` env → the defaults.
# `command=False` keeps the env vars (`KOALATY_POUCH`, `KOALATY_TASKS`) global,
# not per-command.
POUCH_ENV = cyclopts.config.Env("KOALATY_", command=False)
DEFAULT_POUCH = Path("pouch")
DEFAULT_TASKS = Path("tasks")


def derive_driver(*, can_invoke: bool, interactive: bool) -> str:
    """Derive who steers a session: `koalaty` (automated) or `human`.

    A run is human-driven when the task needs interactive judgment or the
    harness has no headless `invoke`; otherwise koalaty drives it.
    """
    if interactive or not can_invoke:
        return "human"
    return "koalaty"
