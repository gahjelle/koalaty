"""Smoke tests verifying the module skeleton is importable and callable."""

from koalaty.__main__ import main


def test_main_is_callable() -> None:
    """main() exists and runs without raising."""
    main()
