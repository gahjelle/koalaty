"""Shared Rich consoles, split by output stream.

Two module-global singletons other modules import by name:

- `stdout` — the primary "product" output a user might pipe or capture
  (the `compare` grid, the `task examples` list).
- `stderr` — diagnostics: status, warnings, "no runs found", and errors.

This split keeps `koalaty compare > grid.txt` clean of chatter. A fileless
Rich Console resolves `sys.stdout`/`sys.stderr` lazily on each write, so these
singletons still honor pytest's `capsys`. See ADR-0007.
"""

from rich.console import Console

__all__ = ["stderr", "stdout"]

stdout = Console()
stderr = Console(stderr=True)
