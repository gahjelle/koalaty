"""Assemble the cyclopts application from the per-area command modules.

`build_app()` wires the handlers defined in the sibling `runs`, `compare`,
`task`, and `config` modules into a single cyclopts `App`. It also registers
the meta-launcher that turns domain errors into friendly Rich boxes (see
ADR-0012).
"""

from typing import Annotated

from cyclopts import App, Parameter

from koalaty.cli import compare, config, runs, task
from koalaty.console import print_error
from koalaty.exceptions import KoalatyError

__all__ = ["build_app"]


def build_app() -> App:
    """Build the cyclopts application with all registered commands."""
    app = App(
        name="koalaty",
        help="Evaluate and compare models inside agent harnesses.",
    )

    app.command(runs.run)
    app.command(runs.start)
    app.command(runs.harvest)
    app.command(compare.compare)
    app.command(config.show_config)

    task_app = App(name="task", help="Author and scaffold task bundles.")
    task_app.command(task.task_new, name="new")
    task_app.command(task.task_examples, name="examples")
    app.command(task_app)

    @app.meta.default
    def launcher(
        *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],
    ) -> None:
        """Run the app, turning domain errors into Rich boxes, not tracebacks.

        Catches `KoalatyError` only: domain failures get a friendly box and a
        non-zero exit, while genuine bugs (`KeyError`, `AttributeError`, ...)
        still raise a full traceback so they stay debuggable.
        """
        try:
            app(tokens)
        except KoalatyError as error:
            print_error(error)
            raise SystemExit(1) from error

    return app
