"""Entry point for the koalaty CLI."""

from koalaty.cli.main import build_app


def main() -> None:
    """Build the koalaty cyclopts app and run it against the command line."""
    build_app()()


if __name__ == "__main__":
    main()
