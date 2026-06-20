"""CLI command for the comparison grid: `compare`.

Sits alongside `koalaty.compare` (the grid module it delegates to); this is the
CLI face of the comparison feed. The pouch is read from `config.pouch` at call
time (see ADR-0010) rather than taken as a CLI flag.
"""

from koalaty import pouch
from koalaty.compare import build_grid, render_grid
from koalaty.config import config
from koalaty.console import stderr, stdout

__all__ = ["compare"]


def compare(
    task: str | None = None,
) -> None:
    """Print a (task x model) grid per harness of the results in the pouch."""
    results = pouch.read_results(config.pouch)
    if not results:
        stderr.print(f"no runs found in {config.pouch}")
        return

    if task is not None:
        results = [result for result in results if result.task == task]
    harnesses = sorted({result.harness for result in results})
    for harness in harnesses:
        stdout.print(render_grid(build_grid(results, harness)))
