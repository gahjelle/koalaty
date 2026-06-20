"""Tests for the packaged configuration registry."""

from pathlib import Path

import pytest

from koalaty.config import config, load_config


def test_settings_default_to_packaged_values() -> None:
    """With no env override, settings fall back to the packaged defaults."""
    loaded = load_config()
    assert loaded.pouch.name == "pouch"
    assert loaded.tasks.name == "tasks"


def test_env_overrides_pouch_and_tasks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KOALATY_POUCH / KOALATY_TASKS override the settings at load time."""
    pouch = tmp_path / "elsewhere-pouch"
    tasks = tmp_path / "elsewhere-tasks"
    monkeypatch.setenv("KOALATY_POUCH", str(pouch))
    monkeypatch.setenv("KOALATY_TASKS", str(tasks))
    loaded = load_config()
    assert loaded.pouch == pouch
    assert loaded.tasks == tasks


def test_invariants_are_a_shared_contract() -> None:
    """Invariant filenames are exposed for scaffold-write / task-load to agree."""
    assert config.task.config_file == "task.toml"
    assert config.task.prompt_file == "prompt.md"
    assert config.result.result_file == "result.json"


def test_config_is_frozen() -> None:
    """The config singleton is immutable."""
    with pytest.raises(Exception, match="frozen"):
        config.task.config_file = "other.toml"
