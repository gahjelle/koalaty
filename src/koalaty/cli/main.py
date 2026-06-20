"""Assemble the cyclopts application from the per-area command modules.

`build_app()` wires the handlers defined in the sibling `runs`, `compare`,
`task`, and `config` modules into a single cyclopts `App`.
"""

from typing import Annotated

from cyclopts import App, Parameter

from koalaty.cli.compare import compare
from koalaty.cli.config import show_config
from koalaty.cli.runs import harvest, run, start
from koalaty.cli.task import task_examples, task_new
from koalaty.console import print_error
from koalaty.exceptions import KoalaError

__all__ = ["build_app"]


def build_app() -> App:
    """Build the cyclopts application with all registered commands."""
    app = App(
        name="koalaty",
        help="Evaluate and compare models inside agent harnesses.",
    )
    app.command(run)
    app.command(start)
    app.command(harvest)
    app.command(compare)
    app.command(show_config)

    task_app = App(name="task", help="Author and scaffold task bundles.")
    task_app.command(task_new, name="new")
    task_app.command(task_examples, name="examples")
    app.command(task_app)

    @app.meta.default
    def launcher(
        *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
    ) -> None:
        """Run the app, turning domain errors into Rich boxes, not tracebacks.

        Catches `KoalaError` only: domain failures get a friendly box and a
        non-zero exit, while genuine bugs (`KeyError`, `AttributeError`, ...)
        still raise a full traceback so they stay debuggable.
        """
        try:
            app(tokens)
        except KoalaError as error:
            print_error(error)
            raise SystemExit(1) from error

    return app
