"""Tests for the repo-specific convention linter."""

import tomllib
from pathlib import Path

from tools.repolint import (
    DEFAULT_PATHS,
    EXEMPT_MODULES,
    check_adr_numbering,
    check_source,
    check_text,
    fix_source,
)

HERE = Path("sample.py")


def _codes(source: str) -> set[str]:
    return {v.code for v in check_source(source, HERE)}


def _text_codes(source: str) -> set[str]:
    return {v.code for v in check_text(source, HERE)}


def test_default_paths_cover_src_and_tests() -> None:
    """The default lint scope covers package sources and tests equally."""
    assert DEFAULT_PATHS == ["src/", "tests/"]


def test_exempt_modules_match_pyproject() -> None:
    """KOA008's module set is loaded from ruff's `exempt-modules`, not hardcoded."""
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    flake8_tc = config["tool"]["ruff"]["lint"]["flake8-type-checking"]
    assert frozenset(flake8_tc["exempt-modules"]) == EXEMPT_MODULES


def test_clean_source_has_no_violations() -> None:
    """Idiomatic source raises nothing."""
    source = '"""A module."""\n\nx: list[int] = []\n'

    assert check_source(source, HERE) == []


def test_flags_future_annotations_import() -> None:
    """A __future__ annotations import is KOA001."""
    assert "KOA001" in _codes("from __future__ import annotations\n")


def test_flags_bare_basemodel_subclass() -> None:
    """A model inheriting BaseModel directly is KOA002."""
    source = "class Thing(BaseModel):\n    pass\n"

    assert "KOA002" in _codes(source)


def test_allows_frozen_model_itself() -> None:
    """FrozenModel is a project base permitted to inherit BaseModel."""
    source = "class FrozenModel(BaseModel):\n    pass\n"

    assert "KOA002" not in _codes(source)


def test_allows_strict_model_itself() -> None:
    """StrictModel is the other project base permitted to inherit BaseModel."""
    source = "class StrictModel(BaseModel):\n    pass\n"

    assert "KOA002" not in _codes(source)


def test_flags_ellipsis_in_protocol_method() -> None:
    """An `...` body in a Protocol method is KOA003."""
    source = (
        "class P(Protocol):\n"
        "    def f(self) -> int:\n"
        '        """Do f."""\n'
        "        ...\n"
    )

    assert "KOA003" in _codes(source)


def test_flags_double_backticks_in_docstring() -> None:
    """Double backticks in a docstring are KOA004."""
    source = '"""See ``graph.toml`` for details."""\n'

    assert "KOA004" in _codes(source)


def test_flags_homogeneous_tuple_annotation() -> None:
    """A `tuple[T, ...]` annotation is KOA005."""
    source = "values: tuple[int, ...] = ()\n"

    assert "KOA005" in _codes(source)


def test_flags_string_forward_ref_return() -> None:
    """A string return forward-ref to the enclosing class is KOA006."""
    source = (
        "class Thing:\n"
        "    @classmethod\n"
        '    def make(cls) -> "Thing":\n'
        "        return cls()\n"
    )

    assert "KOA006" in _codes(source)


def test_fix_removes_future_import_and_single_backticks() -> None:
    """--fix drops the future import and collapses docstring backticks."""
    source = '"""See ``graph.toml``."""\nfrom __future__ import annotations\n'

    fixed = fix_source(source)

    assert "from __future__" not in fixed
    assert "``" not in fixed
    assert check_source(fixed, HERE) == []


def test_flags_possessive_prefix_with_underscore() -> None:
    """A `my` + `_` identifier prefix is KOA007."""
    source = "my" + "_thing = 1\n"

    assert "KOA007" in _text_codes(source)


def test_flags_possessive_prefix_with_hyphen() -> None:
    """A `my` + `-` token prefix is KOA007 (caught in docs too)."""
    source = "see my" + "-task below\n"

    assert "KOA007" in _text_codes(source)


def test_flags_possessive_prefix_pascal_case() -> None:
    """A `My` + uppercase prefix is KOA007."""
    source = "class " + "My" + "Thing: ...\n"

    assert "KOA007" in _text_codes(source)


def test_allows_standalone_possessive_word() -> None:
    """The bare word `my` (no separator) is not KOA007."""
    source = "this is my account\n"

    assert "KOA007" not in _text_codes(source)


def test_clean_text_has_no_possessive_prefix() -> None:
    """Text without the prefix raises nothing."""
    assert check_text("a plain sentence\n", HERE) == []


def test_flags_exempt_module_in_type_checking() -> None:
    """A pathlib import inside TYPE_CHECKING is KOA008."""
    source = (
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from pathlib import Path\n"
    )

    assert "KOA008" in _codes(source)


def test_allows_exempt_module_at_runtime() -> None:
    """A pathlib import at module top level is fine."""
    source = "from pathlib import Path\n\nx = Path('a')\n"

    assert "KOA008" not in _codes(source)


def test_allows_non_exempt_module_in_type_checking() -> None:
    """A non-exempt module inside TYPE_CHECKING is fine."""
    source = (
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Iterator\n"
    )

    assert "KOA008" not in _codes(source)


def _adr_codes(adr_dir: Path, names: list[str]) -> set[str]:
    for name in names:
        (adr_dir / name).write_text("", encoding="utf-8")
    return {v.code for v in check_adr_numbering(adr_dir)}


def test_flags_duplicate_adr_prefix(tmp_path: Path) -> None:
    """Two ADR files sharing a numeric prefix are KOA010."""
    names = ["0001-alpha.md", "0002-beta.md", "0002-gamma.md"]

    assert "KOA010" in _adr_codes(tmp_path, names)


def test_flags_gap_in_adr_numbering(tmp_path: Path) -> None:
    """A missing number in the ADR sequence is KOA011."""
    names = ["0001-alpha.md", "0003-gamma.md"]

    assert "KOA011" in _adr_codes(tmp_path, names)


def test_flags_adr_numbering_not_starting_at_one(tmp_path: Path) -> None:
    """A sequence that starts above 0001 is KOA011."""
    names = ["0002-beta.md", "0003-gamma.md"]

    assert "KOA011" in _adr_codes(tmp_path, names)


def test_clean_adr_directory_has_no_violations(tmp_path: Path) -> None:
    """Unique, gapless ADR numbering from 0001 raises nothing."""
    names = ["0001-alpha.md", "0002-beta.md", "0003-gamma.md"]

    assert _adr_codes(tmp_path, names) == set()
