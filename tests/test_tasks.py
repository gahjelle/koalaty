"""Tests for loading and validating on-disk task bundles."""

from typing import TYPE_CHECKING

import pytest

from koalaty.tasks import TaskError, Turns, load_task

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import TaskWriter


def test_load_defaults_title_from_id(tmp_path: Path, make_task: TaskWriter) -> None:
    """An absent title defaults to the id with dashes spaced and titlecased."""
    tasks = make_task(tmp_path, "drop-bear-trap")
    task = load_task(tasks, "drop-bear-trap")
    assert task.title == "Drop Bear Trap"


def test_load_uses_explicit_title_and_description(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """An explicit title and description are carried onto the task."""
    tasks = make_task(tmp_path, "quokka", title="Quokka Smile", description="Smile.")
    task = load_task(tasks, "quokka")
    assert task.title == "Quokka Smile"
    assert task.description == "Smile."


def test_load_defaults_tags_to_empty(tmp_path: Path, make_task: TaskWriter) -> None:
    """An absent tags list defaults to empty."""
    tasks = make_task(tmp_path, "quokka")
    assert load_task(tasks, "quokka").tags == []


def test_load_defaults_gum_to_inline(tmp_path: Path, make_task: TaskWriter) -> None:
    """An absent [gum] table defaults to an inline gum."""
    tasks = make_task(tmp_path, "quokka")
    assert load_task(tasks, "quokka").gum.type == "inline"


def test_load_parses_git_gum(tmp_path: Path, make_task: TaskWriter) -> None:
    """A git gum carries its url and full-40-hex commit."""
    commit = "a" * 40
    tasks = make_task(
        tmp_path,
        "quokka",
        gum=f"""
        [gum]
        type = "git"
        url = "https://example.com/repo.git"
        commit = "{commit}"
        """,
    )
    gum = load_task(tasks, "quokka").gum
    assert gum.type == "git"
    assert gum.url == "https://example.com/repo.git"
    assert gum.commit == commit


def test_git_gum_rejects_short_sha(tmp_path: Path, make_task: TaskWriter) -> None:
    """A git gum with a short SHA (not 40 hex) is a clear error."""
    tasks = make_task(
        tmp_path,
        "quokka",
        gum="""
        [gum]
        type = "git"
        url = "https://example.com/repo.git"
        commit = "abc123"
        """,
    )
    with pytest.raises(TaskError, match="commit"):
        load_task(tasks, "quokka")


def test_inline_gum_forbids_commit(tmp_path: Path, make_task: TaskWriter) -> None:
    """An inline gum may not carry url/commit."""
    tasks = make_task(
        tmp_path,
        "quokka",
        gum="""
        [gum]
        type = "inline"
        commit = "abc"
        """,
    )
    with pytest.raises(TaskError):
        load_task(tasks, "quokka")


def test_unknown_turns_is_error(tmp_path: Path, make_task: TaskWriter) -> None:
    """An unknown turns value is a clear error."""
    tasks = make_task(tmp_path, "quokka", turns="freeform")
    with pytest.raises(TaskError, match="turns"):
        load_task(tasks, "quokka")


def test_absent_turns_is_error(tmp_path: Path) -> None:
    """A task.toml with no turns key is a clear error."""
    task_dir = tmp_path / "quokka"
    task_dir.mkdir(parents=True)
    (task_dir / "task.toml").write_text("tags = []\n", encoding="utf-8")
    (task_dir / "prompt.md").write_text("Do it.", encoding="utf-8")
    with pytest.raises(TaskError, match="turns"):
        load_task(tmp_path, "quokka")


def test_scripted_splits_into_ordered_turns(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """A scripted prompt splits on bare --- lines into ordered turns."""
    tasks = make_task(
        tmp_path,
        "quokka",
        turns="scripted",
        prompt="First turn.\n---\nSecond turn.\n---\nThird turn.",
    )
    task = load_task(tasks, "quokka")
    assert task.turns is Turns.scripted
    assert task.prompts == ["First turn.", "Second turn.", "Third turn."]


def test_scripted_requires_two_turns(tmp_path: Path, make_task: TaskWriter) -> None:
    """A scripted prompt with fewer than two turns is a clear error."""
    tasks = make_task(
        tmp_path,
        "quokka",
        turns="scripted",
        prompt="Only one turn, no separator.",
    )
    with pytest.raises(TaskError, match="two"):
        load_task(tasks, "quokka")


def test_one_shot_keeps_bare_separator_literal(
    tmp_path: Path,
    make_task: TaskWriter,
) -> None:
    """For one-shot a bare --- is part of the single literal prompt."""
    tasks = make_task(
        tmp_path,
        "quokka",
        prompt="Before.\n---\nAfter.",
    )
    task = load_task(tasks, "quokka")
    assert task.prompts == ["Before.\n---\nAfter."]


def test_load_rejects_bad_task_id(tmp_path: Path, make_task: TaskWriter) -> None:
    """A task id that breaks the id pattern is a clear error."""
    make_task(tmp_path, "quokka")
    with pytest.raises(TaskError, match="Bad_Id"):
        load_task(tmp_path, "Bad_Id")
