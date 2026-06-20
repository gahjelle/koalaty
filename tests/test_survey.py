"""The survey: schema validation, collection via an asker, and harvest storage."""

import io
import json
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from koalaty.adapters.fake import FAKE_SESSION_ID
from koalaty.config import config
from koalaty.runs import harvest_manual, run_automated, start_manual
from koalaty.schemas.survey import Survey
from koalaty.survey import RichAsker, collect_survey
from koalaty.tasks import load_task

if TYPE_CHECKING:
    from collections.abc import Callable

    from cyclopts import App
    from tests.conftest import StubAsker, SurveyStub, TaskWriter


def test_survey_accepts_in_range_ratings() -> None:
    """A survey with 0-5 ratings and notes is accepted."""
    survey = Survey(friction=0, hand_holding=3, frustration=5, notes="went fine")

    assert survey.friction == 0
    assert survey.hand_holding == 3
    assert survey.frustration == 5
    assert survey.notes == "went fine"


@pytest.mark.parametrize("rating", [-1, 6])
def test_survey_rejects_out_of_range_ratings(rating: int) -> None:
    """Ratings outside 0-5 are rejected."""
    with pytest.raises(ValidationError):
        Survey(friction=rating, hand_holding=3, frustration=2, notes="")


def test_collect_survey_assembles_answers_in_order(
    stub_asker: Callable[..., StubAsker],
) -> None:
    """collect_survey maps the asker's ratings to friction/hand_holding/frustration."""
    survey = collect_survey(stub_asker([2, 4, 1], "a bit fiddly"))

    assert survey == Survey(
        friction=2, hand_holding=4, frustration=1, notes="a bit fiddly"
    )


def test_harvest_stores_survey_on_result(
    make_task: TaskWriter,
    stub_asker: Callable[..., StubAsker],
) -> None:
    """harvest_manual collects the survey via the asker and stores it on the result."""
    make_task(config.tasks, "quokka")
    task = load_task(config.tasks, "quokka")
    pending, _ = start_manual(task, "fake", "opus48", pouch_dir=config.pouch)

    result = harvest_manual(
        pending.run_id,
        FAKE_SESSION_ID,
        config.pouch,
        ask=stub_asker([2, 4, 1], "a bit fiddly"),
    )

    expected = Survey(friction=2, hand_holding=4, frustration=1, notes="a bit fiddly")
    assert result.survey == expected
    stored = json.loads((config.pouch / result.run_id / "result.json").read_text())
    assert stored["survey"] == expected.model_dump()


def test_rich_asker_rating_reprompts_until_in_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The interactive rating prompt re-asks until the driver enters a 0-5 value."""
    monkeypatch.setattr("sys.stdin", io.StringIO("9\n7\n3\n"))

    assert RichAsker().rating("rate the friction") == 3


def test_rich_asker_text_returns_free_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """The interactive notes prompt returns the driver's free text."""
    monkeypatch.setattr("sys.stdin", io.StringIO("it felt cramped\n"))

    assert RichAsker().text("any notes?") == "it felt cramped"


def test_automated_run_carries_no_survey(make_task: TaskWriter) -> None:
    """An automated run has no survey: Result.survey is null."""
    make_task(config.tasks, "quokka")
    task = load_task(config.tasks, "quokka")

    result = run_automated(task, "fake", "opus48", pouch_dir=config.pouch)

    assert result.survey is None
    stored = json.loads((config.pouch / result.run_id / "result.json").read_text())
    assert stored["survey"] is None


def test_cli_harvest_stores_survey(
    app: App,
    make_task: TaskWriter,
    survey_stub: SurveyStub,
) -> None:
    """The harvest command runs the (stubbed) survey and stores it on the result."""
    survey_stub.ratings = [3, 5, 2]
    survey_stub.notes = "claustrophobic"
    make_task(config.tasks, "quokka")
    run_id = app(["start", "quokka", "--harness", "fake", "--model", "opus48"])

    app(["harvest", run_id, "--session", FAKE_SESSION_ID])

    stored = json.loads((config.pouch / run_id / "result.json").read_text())
    assert stored["survey"] == {
        "schema_version": 1,
        "friction": 3,
        "hand_holding": 5,
        "frustration": 2,
        "notes": "claustrophobic",
    }
