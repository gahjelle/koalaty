"""Domain schemas: shared types owned by the schemas package.

Every Pydantic model, enum, and type alias that crosses a module boundary
lives here. Behavioral modules import from schemas; schemas never imports
from behavioral modules. See ADR-0004.
"""

from pydantic import BaseModel, ConfigDict

__all__ = ["FrozenModel"]


class FrozenModel(BaseModel):
    """Immutable, strict base for koalaty's models.

    Forbids unknown fields and freezes instances, so a record can't pick up
    stray keys or be mutated after it is assembled.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
