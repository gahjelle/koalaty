"""Comparison: build a (task x model) grid per harness and render it."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.table import Table

from koalaty.schemas.result import SessionStatus

__all__ = ["Grid", "Tally", "build_grid", "render_grid"]

if TYPE_CHECKING:
    from collections.abc import Iterable

    from koalaty.schemas.result import Result


@dataclass(frozen=True, kw_only=True)
class Tally:
    """Session-status counts for one (task, model) cell of a grid.

    Counts how each session *ended* (`completed` vs not) — not a success/failure
    verdict, which paws/survey decide later (see ADR-0015).
    """

    completed: int = 0
    incomplete: int = 0

    def add(self, status: SessionStatus) -> Tally:
        """Return a new tally with `status` counted in."""
        if status is SessionStatus.completed:
            return Tally(completed=self.completed + 1, incomplete=self.incomplete)
        return Tally(completed=self.completed, incomplete=self.incomplete + 1)


@dataclass(kw_only=True)
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
        tallies[key] = tallies[key].add(result.session_status)
    return Grid(harness=harness, tallies=dict(tallies))


def render_cell(tally: Tally | None) -> str:
    """Render a cell: colored tally, or a dim dash for an empty combo."""
    if tally is None:
        return "[dim]\N{EN DASH}[/dim]"
    if tally.incomplete == 0:
        return f"[green]{tally.completed} ✓[/green]"
    if tally.completed == 0:
        return f"[red]{tally.incomplete} ✗[/red]"
    return f"[yellow]{tally.completed} ✓ / {tally.incomplete} ✗[/yellow]"


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
