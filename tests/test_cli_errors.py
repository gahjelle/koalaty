"""Tests for the CLI error-handling seam: friendly boxes via the meta launcher.

These drive the app through `build_app().meta(...)` — the real entry point
`__main__.main()` uses — so they exercise the domain-error catch that turns a
`KoalaError` into a Rich box instead of a traceback.
"""

from pathlib import Path

import pytest

from koalaty.cli.main import build_app


def test_domain_error_prints_box_and_exits(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A KoalaError raised in a command body becomes a Rich box, exit code 1."""
    app = build_app()
    with pytest.raises(SystemExit) as excinfo:
        app.meta(
            [
                "harvest",
                "wombat-fake-opus48-x",
                "--session",
                "s",
                "--pouch",
                str(tmp_path),
            ]
        )

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "Error" in err
    assert "wombat-fake-opus48-x" in err


def test_genuine_bug_still_raises_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-KoalaError escapes the launcher uncaught, keeping bugs debuggable."""

    def boom(*_args: object, **_kwargs: object) -> object:
        msg = "a genuine bug"
        raise RuntimeError(msg)

    monkeypatch.setattr("koalaty.cli.runs.harvest_manual", boom)
    app = build_app()
    with pytest.raises(RuntimeError, match="a genuine bug"):
        app.meta(["harvest", "any-run-id", "--session", "s", "--pouch", str(tmp_path)])


def _error_frame(err: str) -> list[str]:
    """Return a box's border lines (the framing, not the message text)."""
    return [line for line in err.splitlines() if set(line.strip()) & set("╭╮╰╯")]


def test_domain_box_matches_cyclopts_parse_box(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The domain-error box and cyclopts' parse-error box share their framing."""
    app = build_app()

    # A parse-stage error: cyclopts renders its own red `Error` box and exits.
    with pytest.raises(SystemExit):
        app.meta(["definitely-not-a-command"])
    parse_frame = _error_frame(capsys.readouterr().err)

    # A domain error caught at the launcher seam, rendered by `print_error`.
    with pytest.raises(SystemExit):
        app.meta(
            [
                "harvest",
                "wombat-fake-opus48-x",
                "--session",
                "s",
                "--pouch",
                str(tmp_path),
            ]
        )
    domain_frame = _error_frame(capsys.readouterr().err)

    assert parse_frame == domain_frame
