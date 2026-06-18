"""Comparison: build a (model x harness) grid per task and render it."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.table import Table

from koalaty.schemas.result import Outcome

__all__ = ["Grid", "Tally", "build_grid", "render_grid"]

if TYPE_CHECKING:
    from collections.abc import Iterable

    from koalaty.schemas.result import Result


@dataclass(frozen=True)
class Tally:
    """The outcome counts for one (model, harness) cell of a grid."""

    success: int = 0
    failure: int = 0

    def add(self, outcome: Outcome) -> Tally:
        """Return a new tally with `outcome` counted in."""
        if outcome is Outcome.success:
            return Tally(self.success + 1, self.failure)
        return Tally(self.success, self.failure + 1)


@dataclass
class Grid:
    """A single task's comparison grid: `(model, harness) -> Tally`."""

    task: str
    tallies: dict[tuple[str, str], Tally] = field(default_factory=dict)

    @property
    def models(self) -> list[str]:
        """The distinct models present, in sorted order."""
        return sorted({model for model, _ in self.tallies})

    @property
    def harnesses(self) -> list[str]:
        """The distinct harnesses present, in sorted order."""
        return sorted({harness for _, harness in self.tallies})


def build_grid(results: Iterable[Result], task: str) -> Grid:
    """Tally the results for `task` into a (model x harness) grid (pure)."""
    tallies: dict[tuple[str, str], Tally] = defaultdict(Tally)
    for result in results:
        if result.task != task:
            continue
        key = (result.model, result.harness)
        tallies[key] = tallies[key].add(result.outcome)
    return Grid(task=task, tallies=dict(tallies))


def render_cell(tally: Tally | None) -> str:
    """Render a cell: colored tally, or a dim dash for an empty combo."""
    if tally is None:
        return "[dim]–[/dim]"  # noqa: RUF001 — en dash is the intended empty-cell glyph
    if tally.failure == 0:
        return f"[green]{tally.success} ✓[/green]"
    if tally.success == 0:
        return f"[red]{tally.failure} ✗[/red]"
    return f"[yellow]{tally.success} ✓ / {tally.failure} ✗[/yellow]"


def render_grid(grid: Grid) -> Table:
    """Render `grid` as a rich table: rows = models, columns = harnesses."""
    table = Table(title=grid.task)
    table.add_column("model")
    harnesses = grid.harnesses
    for harness in harnesses:
        table.add_column(harness)
    for model in grid.models:
        cells = [
            render_cell(grid.tallies.get((model, harness))) for harness in harnesses
        ]
        table.add_row(model, *cells)
    return table
