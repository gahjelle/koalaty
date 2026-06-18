"""Configuration: pouch-location binding and driver derivation."""

from pathlib import Path

import cyclopts

# Pouch precedence: ``--pouch`` → ``KOALATY_POUCH`` env → ``./pouch/``.
# ``command=False`` keeps the env var ``KOALATY_POUCH`` (not per-command).
POUCH_ENV = cyclopts.config.Env("KOALATY_", command=False)
DEFAULT_POUCH = Path("pouch")


def derive_driver(*, can_invoke: bool, interactive: bool) -> str:
    """Derive who steers a session: `koalaty` (automated) or `human`.

    A run is human-driven when the task needs interactive judgment or the
    harness has no headless `invoke`; otherwise koalaty drives it.
    """
    if interactive or not can_invoke:
        return "human"
    return "koalaty"
