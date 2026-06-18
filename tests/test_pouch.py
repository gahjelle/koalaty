"""Focused unit tests for run-id minting and collision regeneration."""

from datetime import UTC, datetime

from koalaty.pouch import mint_run_id

_NOW = datetime(2026, 6, 18, 9, 30, tzinfo=UTC)


def test_mint_run_id_has_canonical_shape() -> None:
    """The minted id places the date after the model and is dash-free per field."""
    run_id = mint_run_id(
        "quokka",
        "fake",
        "opus48",
        now=_NOW,
        is_taken=lambda _run_id: False,
        new_shortid=lambda: "abc123",
    )
    assert run_id == "quokka-fake-opus48-20260618-abc123"


def test_mint_run_id_regenerates_shortid_on_collision() -> None:
    """A taken id triggers regeneration with a fresh shortid."""
    shortids = iter(["aaaaaa", "bbbbbb"])
    run_id = mint_run_id(
        "quokka",
        "fake",
        "opus48",
        now=_NOW,
        is_taken=lambda candidate: candidate.endswith("aaaaaa"),
        new_shortid=lambda: next(shortids),
    )
    assert run_id == "quokka-fake-opus48-20260618-bbbbbb"
