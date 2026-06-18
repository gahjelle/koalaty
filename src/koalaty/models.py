"""The shared pydantic base for every koalaty model."""

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Immutable, strict base for koalaty's models.

    Forbids unknown fields and freezes instances, so a record can't pick up
    stray keys or be mutated after it is assembled.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
