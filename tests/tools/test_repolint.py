"""Tests for the repo-specific convention linter."""

from pathlib import Path

from tools.repolint import DEFAULT_PATHS, check_source, fix_source

HERE = Path("sample.py")


def _codes(source: str) -> set[str]:
    return {v.code for v in check_source(source, HERE)}


def test_default_paths_cover_src_and_tests() -> None:
    """The default lint scope covers package sources and tests equally."""
    assert DEFAULT_PATHS == ["src/", "tests/"]


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


def test_allows_strict_model_itself() -> None:
    """FrozenModel is the one class permitted to inherit BaseModel."""
    source = "class FrozenModel(BaseModel):\n    pass\n"

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
