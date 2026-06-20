"""End-to-end tests of bundled example tasks: copying them and listing them."""

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from koalaty.exceptions import TaskScaffoldError
from koalaty.tasks import load_task

if TYPE_CHECKING:
    from cyclopts import App


def test_bundled_examples_ship_one_shot_and_scripted(app: App, tmp_path: Path) -> None:
    """The bundled examples include a one-shot `quokka` and a scripted task."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "--from-example", "quokka"])
    app(["task", "new", "--from-example", "wombat"])

    quokka = load_task(tasks, "quokka")
    wombat = load_task(tasks, "wombat")
    assert quokka.turns.value == "one-shot"
    assert wombat.turns.value == "scripted"
    # The scripted example splits into multiple turns on bare `---` lines.
    assert len(wombat.prompts) >= 2


def test_from_example_defaults_id_to_example_name(app: App, tmp_path: Path) -> None:
    """`task new --from-example <name>` copies into `tasks/<name>/` verbatim."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "--from-example", "quokka"])

    task_dir = tasks / "quokka"
    assert (task_dir / "task.toml").is_file()
    assert (task_dir / "prompt.md").read_text(encoding="utf-8").strip()
    config = tomllib.loads((task_dir / "task.toml").read_text(encoding="utf-8"))
    assert config["turns"] == "one-shot"


def test_from_example_explicit_id_copies_into_that_id(app: App, tmp_path: Path) -> None:
    """`task new <id> --from-example <name>` copies into `tasks/<id>/`."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "greeter", "--from-example", "quokka"])

    assert (tasks / "greeter" / "prompt.md").is_file()
    assert not (tasks / "quokka").exists()
    # The destination id drives the loaded id (and so its default title).
    loaded = load_task(tasks, "greeter")
    assert loaded.id == "greeter"


def test_from_example_title_defaults_from_id_when_toml_omits_it(
    app: App,
    tmp_path: Path,
) -> None:
    """A copied task whose `task.toml` lacks `title` defaults it from the id."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "--from-example", "quokka"])

    toml = tasks / "quokka" / "task.toml"
    raw = tomllib.loads(toml.read_text(encoding="utf-8"))
    del raw["title"]
    lines = [
        f'turns = "{raw["turns"]}"',
        "tags = []",
        f'description = "{raw["description"]}"',
        "",
        "[gum]",
        f'type = "{raw["gum"]["type"]}"',
    ]
    toml.write_text("\n".join(lines) + "\n", encoding="utf-8")

    loaded = load_task(tasks, "quokka")
    assert loaded.title == "Quokka"


def test_from_example_title_defaults_from_explicit_id_when_toml_omits_it(
    app: App,
    tmp_path: Path,
) -> None:
    """`task new <id> --from-example <name>` defaults title from <id>, not <name>."""
    tasks = tmp_path / "tasks"
    app(["task", "new", "greeter", "--from-example", "quokka"])

    toml = tasks / "greeter" / "task.toml"
    raw = tomllib.loads(toml.read_text(encoding="utf-8"))
    del raw["title"]
    lines = [
        f'turns = "{raw["turns"]}"',
        "tags = []",
        f'description = "{raw["description"]}"',
        "",
        "[gum]",
        f'type = "{raw["gum"]["type"]}"',
    ]
    toml.write_text("\n".join(lines) + "\n", encoding="utf-8")

    loaded = load_task(tasks, "greeter")
    assert loaded.title == "Greeter"


def test_new_without_id_or_example_errors(app: App, tmp_path: Path) -> None:
    """`task new` with neither an id nor --from-example is an error."""
    tasks = tmp_path / "tasks"
    with pytest.raises(TaskScaffoldError):
        app(["task", "new"])
    assert not tasks.exists() or list(tasks.iterdir()) == []


def test_unknown_example_errors_with_available_list(app: App, tmp_path: Path) -> None:
    """An unknown example name fails and lists the available examples."""
    tasks = tmp_path / "tasks"
    with pytest.raises(TaskScaffoldError, match="quokka") as excinfo:
        app(["task", "new", "--from-example", "nope"])
    assert "nope" in str(excinfo.value)
    assert "wombat" in str(excinfo.value)
    assert not tasks.exists() or list(tasks.iterdir()) == []


def test_from_example_refuses_to_overwrite_existing(app: App, tmp_path: Path) -> None:
    """Copying obeys the collision rule from #18 and leaves the target untouched."""
    tasks = tmp_path / "tasks"
    existing = tasks / "quokka"
    existing.mkdir(parents=True)
    (existing / "prompt.md").write_text("hand-written", encoding="utf-8")

    with pytest.raises(TaskScaffoldError, match="already exists"):
        app(["task", "new", "--from-example", "quokka"])

    assert (existing / "prompt.md").read_text(encoding="utf-8") == "hand-written"
    assert list(existing.iterdir()) == [existing / "prompt.md"]


def test_from_example_rejects_invalid_destination_id(app: App, tmp_path: Path) -> None:
    """Copying obeys the id-validation rule from #18 before writing anything."""
    tasks = tmp_path / "tasks"
    with pytest.raises(TaskScaffoldError, match="Bad_Id"):
        app(["task", "new", "Bad_Id", "--from-example", "quokka"])
    assert not tasks.exists() or list(tasks.iterdir()) == []


def test_examples_command_lists_name_and_title(
    app: App,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`task examples` lists each bundled example with its name and title."""
    app(["task", "examples"])
    out = capsys.readouterr().out
    assert "quokka" in out
    assert "Quokka greeter" in out
    assert "wombat" in out
    assert "Wombat burrow" in out


def test_from_example_round_trips_through_run_and_compare(
    app: App,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Copy a scripted example, then run, then compare — the headline round-trip."""
    pouch = tmp_path / "pouch"
    app(["task", "new", "--from-example", "wombat"])

    run_id = app(["run", "wombat", "--harness", "fake", "--model", "opus48"])
    assert (pouch / run_id / "result.json").is_file()

    capsys.readouterr()
    app(["compare"])
    assert "wombat" in capsys.readouterr().out
