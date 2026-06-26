"""koalaty's configuration registry: the packaged `koalaty.toml` singleton.

`load_config()` reads the packaged TOML registry via configaroo, overlays the
two settings env vars (`KOALATY_POUCH`, `KOALATY_TASKS`), and validates it into
a frozen `Config`. `config` is the import-time singleton every module reads from
— both the fixed invariants and the resolved settings (the CLI defaults
`--pouch`/`--tasks` to `config.pouch`/`config.tasks`). See ADR-0007.
"""

from pathlib import Path

from configaroo import Configuration

from koalaty.schemas.config import Config

__all__ = ["config", "load_config"]

TOML_PATH = Path(__file__).parent / "koalaty.toml"

# configaroo owns file + env + defaults; only the two settings keys are env-mapped.
# Nested invariant sections are never env-mapped, which is what keeps them fixed.
SETTINGS_ENVS = {"POUCH": "pouch", "TASKS": "tasks"}


def load_config() -> Config:
    """Load the registry, overlay the settings env vars, validate into `Config`."""
    return (
        Configuration.from_file(TOML_PATH)
        .add_envs(SETTINGS_ENVS, prefix="KOALATY_")
        .with_model(Config)
    )


config = load_config()
