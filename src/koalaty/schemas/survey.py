"""Survey schema: the first-person survey stored on a manual result.

The driver answers the survey at harvest (manual runs only); it is stored on
the `Result` and is null for automated runs. The question set may evolve later
(issue #1 defers calibration), so the survey carries its own `schema_version`.
"""

from typing import Annotated

from pydantic import Field

from koalaty.schemas import FrozenModel

__all__ = ["SURVEY_SCHEMA_VERSION", "Rating", "Survey"]

SURVEY_SCHEMA_VERSION = 1

# A survey rating: an integer on the 0 (none) to 5 (a lot) scale.
Rating = Annotated[int, Field(ge=0, le=5)]


class Survey(FrozenModel):
    """First-person feedback from the human driver on how the session felt.

    Captured at harvest for manual runs only and stored on the `Result`. The
    three ratings are 0-5 (out-of-range values are rejected); `notes` is free
    text. Not part of paws.
    """

    schema_version: int = SURVEY_SCHEMA_VERSION
    friction: Rating
    hand_holding: Rating
    frustration: Rating
    notes: str = ""
