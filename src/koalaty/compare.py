"""Comparison: build a (task x model) grid per harness and render it."""

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
    """The outcome counts for one (task, model) cell of a grid."""

    success: int = 0
    failure: int = 0

    def add(self, outcome: Outcome) -> Tally:
        """Return a new tally with `outcome` counted in."""
        if outcome is Outcome.success:
            return Tally(self.success + 1, self.failure)
        return Tally(self.success, self.failure + 1)


@dataclass
class Grid:
    """A single harness's comparison grid: `(task, model) -> Tally`."""

    harness: str
    tallies: dict[tuple[str, str], Tally] = field(default_factory=dict)

    @property
    def tasks(self) -> list[str]:
        """The distinct tasks present, in sorted order."""
        return sorted({task for task, _ in self.tallies})

    @property
    def models(self) -> list[str]:
        """The distinct models present, in sorted order."""
        return sorted({model for _, model in self.tallies})


def build_grid(results: Iterable[Result], harness: str) -> Grid:
    """Tally the results for `harness` into a (task x model) grid (pure)."""
    tallies: dict[tuple[str, str], Tally] = defaultdict(Tally)
    for result in results:
        if result.harness != harness:
            continue
        key = (result.task, result.model)
        tallies[key] = tallies[key].add(result.outcome)
    return Grid(harness=harness, tallies=dict(tallies))


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
    """Render `grid` as a rich table: rows = tasks, columns = models."""
    table = Table(title=grid.harness)
    table.add_column("task")
    models = grid.models
    for model in models:
        table.add_column(model)
    for task in grid.tasks:
        cells = [render_cell(grid.tallies.get((task, model))) for model in models]
        table.add_row(task, *cells)
    return table
