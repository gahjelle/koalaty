"""Shared test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from koalaty.cli.main import build_app

if TYPE_CHECKING:
    from cyclopts import App


@pytest.fixture
def app() -> App:
    """Return a koalaty app wired for clean in-process invocation in tests.

    ``exit_on_error=False`` lets validation errors raise instead of exiting, and
    ``result_action="return_value"`` returns the command's value (e.g. run id).
    """
    app = build_app()
    app.exit_on_error = False
    app.result_action = "return_value"
    return app
