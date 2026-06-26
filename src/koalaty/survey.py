"""The survey: its question set and the asker seam that collects it.

`collect_survey` owns the first-person question set and assembles a `Survey`
from an injected `Asker`. The asker is the seam: the CLI wires an interactive
Rich prompter, while tests pass a stub. Keeping the question set here (not in
the CLI) lets tests exercise the real assembly and range validation.
"""

from typing import Protocol

from rich.prompt import IntPrompt, Prompt

from koalaty.console import stderr
from koalaty.schemas.survey import Survey

__all__ = ["Asker", "RichAsker", "collect_survey", "make_asker"]

# The 0-5 rating choices an interactive asker enforces, mirroring `Survey`'s
# `Rating` bound so the prompt re-asks rather than letting the model reject.
RATING_CHOICES = [str(value) for value in range(6)]

FRICTION_PROMPT = (
    "Friction — how much did the harness get in your way? (0 none … 5 a lot)"
)
HAND_HOLDING_PROMPT = (
    "Hand-holding — how much did you have to steer the model? (0 none … 5 a lot)"
)
FRUSTRATION_PROMPT = "Frustration — how frustrating was the session? (0 none … 5 a lot)"
NOTES_PROMPT = "Notes — anything else about how the session felt?"


class Asker(Protocol):
    """The survey-collection seam: ask one rating or one free-text question.

    `rating` must return an integer answer (the interactive implementation
    re-prompts until the driver gives a valid one); `text` returns free text.
    """

    def rating(self, prompt: str) -> int:
        """Ask `prompt` and return the driver's integer rating."""

    def text(self, prompt: str) -> str:
        """Ask `prompt` and return the driver's free-text answer."""


def collect_survey(asker: Asker) -> Survey:
    """Assemble a `Survey` by putting the question set to `asker` in order.

    The three ratings are validated to 0-5 by the `Survey` model; an
    interactive asker also re-prompts so out-of-range input never reaches here.
    """
    return Survey(
        friction=asker.rating(FRICTION_PROMPT),
        hand_holding=asker.rating(HAND_HOLDING_PROMPT),
        frustration=asker.rating(FRUSTRATION_PROMPT),
        notes=asker.text(NOTES_PROMPT),
    )


class RichAsker:
    """An `Asker` that prompts the driver interactively via Rich.

    Prompts go to the shared `stderr` console so the harvested run id stays the
    only thing on stdout (ADR-0008). `rating` constrains input to 0-5 and re-asks
    on anything else; `text` accepts free text and defaults to empty.
    """

    def rating(self, prompt: str) -> int:
        """Prompt for a 0-5 rating, re-asking until the driver gives one."""
        return IntPrompt.ask(prompt, console=stderr, choices=RATING_CHOICES)

    def text(self, prompt: str) -> str:
        """Prompt for free text, defaulting to empty if the driver just hits enter."""
        return Prompt.ask(prompt, console=stderr, default="")


def make_asker() -> Asker:
    """Return the interactive asker the CLI wires into harvest.

    A factory so the CLI reads it at call time and tests can swap in a stub,
    keeping the survey hermetic (mirrors how the fake adapter is the test seam).
    """
    return RichAsker()
