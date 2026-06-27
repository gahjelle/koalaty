"""Shared Rich consoles, split by output stream.

Two module-global singletons other modules import by name:

- `stdout` — the primary "product" output a user might pipe or capture
  (the `compare` grid, the `task examples` list).
- `stderr` — diagnostics: status, warnings, "no runs found", and errors.

This split keeps `koalaty compare > grid.txt` clean of chatter. A fileless
Rich Console resolves `sys.stdout`/`sys.stderr` lazily on each write, so these
singletons still honor pytest's `capsys`. See ADR-0008.
"""

from rich.console import Console
from rich.panel import Panel

__all__ = ["print_error", "stderr", "stdout"]

stdout = Console()
stderr = Console(stderr=True)


def print_error(error: Exception) -> None:
    """Print a domain error in a red `Error` panel on stderr.

    Mimics the red box cyclopts renders for parse-stage errors, so a domain
    error caught at the execution seam (the CLI meta launcher) looks identical
    to a parse error rather than dumping a raw traceback.
    """
    stderr.print(
        Panel(str(error), title="Error", title_align="left", border_style="red"),
    )
