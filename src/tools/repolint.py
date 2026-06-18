"""Repo-specific convention checks ruff and ty cannot express.

Encodes the rules in the `repo-coding-conventions` policy:

  KOA001  no `from __future__ import annotations` (3.14 evaluates annotations lazily)
  KOA002  Pydantic models inherit `FrozenModel`, never `BaseModel` directly
  KOA003  `Protocol` methods omit `...` — the docstring is body enough
  KOA004  docstrings use single backticks, never double
  KOA005  homogeneous sequences use `list`, not `tuple[T, ...]`
  KOA006  return `Self`, never a string forward-ref to the enclosing class

Run: `uv run python -m tools.repolint [paths...]` (defaults to `src/` and `tests/`).
Pass `--fix` to auto-apply the safe textual fixes (KOA001, KOA004).
"""

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

DEFAULT_PATHS = ["src/", "tests/"]
DOUBLE_BACKTICK = "`" * 2
FUTURE_ANNOTATIONS = "from __future__ import annotations"


@dataclass(frozen=True)
class Violation:
    """A single convention breach at a source location."""

    path: Path
    line: int
    col: int
    code: str
    message: str

    def render(self) -> str:
        """Format as `path:line:col: CODE message` (ruff-style)."""
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def _docstring_node(node: ast.AST) -> ast.Constant | None:
    """Return the docstring Constant of node, if it has one."""
    body = getattr(node, "body", None)
    if not isinstance(body, list) or not body or not isinstance(body[0], ast.Expr):
        return None
    value = body[0].value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value
    return None


def _is_named(node: ast.expr, name: str) -> bool:
    """Report whether node is a bare `name` or an attribute access ending in `name`."""
    if isinstance(node, ast.Name):
        return node.id == name
    return isinstance(node, ast.Attribute) and node.attr == name


def _check_future_import(tree: ast.Module, path: Path) -> Iterator[Violation]:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
        ):
            yield Violation(
                path,
                node.lineno,
                node.col_offset + 1,
                "KOA001",
                "remove `from __future__ import annotations`",
            )


def _check_strict_model(tree: ast.Module, path: Path) -> Iterator[Violation]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name == "FrozenModel":
            continue
        if any(_is_named(base, "BaseModel") for base in node.bases):
            yield Violation(
                path,
                node.lineno,
                node.col_offset + 1,
                "KOA002",
                f"`{node.name}` must inherit `FrozenModel`, not `BaseModel`",
            )


def _check_protocol_ellipsis(tree: ast.Module, path: Path) -> Iterator[Violation]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_is_named(base, "Protocol") for base in node.bases):
            continue
        for method in node.body:
            if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                yield from _ellipsis_in_method(method, path)


def _ellipsis_in_method(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
    path: Path,
) -> Iterator[Violation]:
    for stmt in method.body:
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is Ellipsis
        ):
            yield Violation(
                path,
                stmt.lineno,
                stmt.col_offset + 1,
                "KOA003",
                "drop `...` from the Protocol method; the docstring is enough",
            )


def _check_double_backticks(tree: ast.Module, path: Path) -> Iterator[Violation]:
    for node in ast.walk(tree):
        doc = _docstring_node(node)
        if doc is None or not isinstance(doc.value, str):
            continue
        if DOUBLE_BACKTICK in doc.value:
            yield Violation(
                path,
                doc.lineno,
                doc.col_offset + 1,
                "KOA004",
                "use single backticks in docstrings, not double",
            )


def _check_homogeneous_tuple(tree: ast.Module, path: Path) -> Iterator[Violation]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript) or not _is_named(node.value, "tuple"):
            continue
        sliced = node.slice
        if isinstance(sliced, ast.Tuple) and any(
            isinstance(elt, ast.Constant) and elt.value is Ellipsis
            for elt in sliced.elts
        ):
            yield Violation(
                path,
                node.lineno,
                node.col_offset + 1,
                "KOA005",
                "use `list[T]` for homogeneous sequences, not `tuple[T, ...]`",
            )


def _check_self_forward_ref(tree: ast.Module, path: Path) -> Iterator[Violation]:
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            returns = method.returns
            if isinstance(returns, ast.Constant) and returns.value == cls.name:
                yield Violation(
                    path,
                    returns.lineno,
                    returns.col_offset + 1,
                    "KOA006",
                    f'return `Self`, not the forward-ref `"{cls.name}"`',
                )


CHECKS = (
    _check_future_import,
    _check_strict_model,
    _check_protocol_ellipsis,
    _check_double_backticks,
    _check_homogeneous_tuple,
    _check_self_forward_ref,
)


def check_source(source: str, path: Path) -> list[Violation]:
    """Return every convention violation in source (parsed from path)."""
    tree = ast.parse(source, filename=str(path))
    return [v for check in CHECKS for v in check(tree, path)]


def fix_source(source: str) -> str:
    """Apply the safe textual fixes (KOA004 single backticks, KOA001 future import)."""
    tree = ast.parse(source)
    docstring_lines = {
        line
        for node in ast.walk(tree)
        if (doc := _docstring_node(node)) is not None
        for line in range(doc.lineno, (doc.end_lineno or doc.lineno) + 1)
    }
    fixed: list[str] = []
    for number, line in enumerate(source.splitlines(keepends=True), start=1):
        if line.strip() == FUTURE_ANNOTATIONS:
            continue
        emitted = (
            line.replace(DOUBLE_BACKTICK, "`") if number in docstring_lines else line
        )
        fixed.append(emitted)
    return "".join(fixed)


def iter_python_files(paths: list[str]) -> Iterator[Path]:
    """Yield every `.py` file under the given paths (files or directories)."""
    for raw in paths:
        root = Path(raw)
        if root.is_file():
            yield root
        else:
            yield from sorted(root.rglob("*.py"))


def main(argv: list[str] | None = None) -> int:
    """Lint the given paths; return 1 if any violations remain."""
    parser = argparse.ArgumentParser(description="Repo-specific convention checks.")
    parser.add_argument("paths", nargs="*", default=list(DEFAULT_PATHS))
    parser.add_argument("--fix", action="store_true", help="apply safe textual fixes")
    args = parser.parse_args(argv)

    violations: list[Violation] = []
    for file in iter_python_files(args.paths or list(DEFAULT_PATHS)):
        source = file.read_text(encoding="utf-8")
        if args.fix:
            fixed = fix_source(source)
            if fixed != source:
                file.write_text(fixed, encoding="utf-8")
                source = fixed
        violations.extend(check_source(source, file))

    for violation in violations:
        sys.stdout.write(violation.render() + "\n")
    if violations:
        sys.stdout.write(f"\nFound {len(violations)} convention violation(s).\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
