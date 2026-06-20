"""CLI command for inspecting configuration: `show_config`.

Sits alongside the `koalaty.config` package (the registry it prints); this is
the CLI face of the configuration registry.
"""

from configaroo import print_configuration

from koalaty.config import config

__all__ = ["show_config"]


def show_config(section: str | None = None) -> None:
    """Print the current configuration registry to the console."""
    print_configuration(config, section)
