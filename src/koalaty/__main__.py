"""Entry point for the koalaty CLI."""

from koalaty.cli.main import build_app


def main() -> None:
    """Build the koalaty cyclopts app and run it against the command line.

    Invokes the app through its meta launcher so domain errors surface as Rich
    boxes (see `build_app`) rather than tracebacks.
    """
    build_app().meta()


if __name__ == "__main__":
    main()
