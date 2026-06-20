"""Assemble the cyclopts application from the per-area command modules.

`build_app()` wires the handlers defined in the sibling `runs`, `compare`,
`task`, and `config` modules into a single cyclopts `App`. It also builds the
dynamic task `Literal` for `run`/`start` from the tasks currently on disk, so an
unknown task is rejected at parse time with a friendly box (see ADR-0010).
"""

import types
from typing import Annotated, Literal

from cyclopts import App, Parameter

from koalaty.cli.compare import compare
from koalaty.cli.config import show_config
from koalaty.cli.runs import harvest, run, start
from koalaty.cli.task import task_examples, task_new
from koalaty.config import config
from koalaty.console import print_error
from koalaty.exceptions import KoalaError
from koalaty.tasks import list_task_ids

__all__ = ["build_app"]


def with_task_choices(
    func: types.FunctionType,
    task_type: object,
) -> types.FunctionType:
    """Return a copy of `func` whose `task` parameter is annotated `task_type`.

    cyclopts derives a parameter's choices from its annotation, so to make the
    task ids a build-time choice list we clone the handler and swap the `task`
    annotation for a `Literal` of the known ids. The annotation is set to the
    real type object (not a name), so cyclopts resolves it without needing the
    closure in scope. The original module-level function is left untouched.
    """
    clone = types.FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=func.__defaults__,
        closure=func.__closure__,
    )
    clone.__kwdefaults__ = func.__kwdefaults__
    clone.__dict__.update(func.__dict__)
    clone.__annotations__ = {**func.__annotations__, "task": task_type}
    clone.__doc__ = func.__doc__
    return clone


def build_app() -> App:
    """Build the cyclopts application with all registered commands."""
    app = App(
        name="koalaty",
        help="Evaluate and compare models inside agent harnesses.",
    )

    # `run`/`start` reject unknown task ids up front via a dynamic Literal built
    # from the tasks on disk now; an empty/missing tasks dir falls back to `str`
    # (so the load-time error path still gives a clean box).
    task_ids = list_task_ids(config.tasks)
    # The Literal is built from a runtime tuple, which static analysis can't form.
    task_type: object = str
    if task_ids:
        task_type = Literal[tuple(task_ids)]  # ty: ignore[invalid-type-form]
    app.command(with_task_choices(run, task_type))
    app.command(with_task_choices(start, task_type))
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
