"""Provenance schema: the reproducibility metadata stamped on a result.

What you would need to reproduce a run: which harness build drove it, which
model, on what date, against which gum baseline. `model` and `date` echo the
result's own fields deliberately — provenance is a self-contained record of the
conditions, not a pointer into them.
"""

from datetime import date

from koalaty.schemas import FrozenModel

__all__ = ["Provenance"]


class Provenance(FrozenModel):
    """The conditions a run happened under, for later reproduction.

    `harness_version` is the harness CLI build observed at harvest; `gum_commit`
    is the pinned commit of a git gum, or `None` for an inline gum that ships in
    the task bundle itself.
    """

    harness_version: str
    model: str
    date: date
    gum_commit: str | None = None
