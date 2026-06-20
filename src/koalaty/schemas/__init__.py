"""Domain schemas: shared types owned by the schemas package.

Every Pydantic model, enum, and type alias that crosses a module boundary
lives here. Behavioral modules import from schemas; schemas never imports
from behavioral modules. See ADR-0004.
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["FrozenModel", "StrictModel"]


class StrictModel(BaseModel):
    """Strict but mutable base for koalaty's models.

    Forbids unknown fields (so a record can't pick up stray keys) but leaves
    instances mutable. `Config` uses this so tests can monkeypatch its settings
    (`config.tasks`, `config.pouch`); see ADR-0010.
    """

    model_config = ConfigDict(extra="forbid")


class FrozenModel(StrictModel):
    """Immutable, strict base for koalaty's models.

    Adds freezing to `StrictModel`, so a record can't be mutated after it is
    assembled. Most domain records inherit this.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
