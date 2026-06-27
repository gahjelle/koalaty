"""Repo-specific convention checks ruff and ty cannot express.

Encodes the rules in the `repo-coding-conventions` policy:

  KOA001  no `from __future__ import annotations` (3.14 evaluates annotations lazily)
  KOA002  Pydantic models inherit `FrozenModel`/`StrictModel`, never `BaseModel`
  KOA003  `Protocol` methods omit `...` — the docstring is body enough
  KOA004  docstrings use single backticks, never double
  KOA005  homogeneous sequences use `list`, not `tuple[T, ...]`
  KOA006  return `Self`, never a string forward-ref to the enclosing class
  KOA007  no possessive `my` prefix (`my`+_/-, `My`+uppercase) in code or docs
  KOA008  ruff-exempt modules stay at runtime, not in TYPE_CHECKING
  KOA009  at most 3 positional parameters — use keyword-only args beyond that
  KOA010  no duplicate numeric prefixes among `docs/adr/` filenames
  KOA011  ADR numbers are consecutive from `0001` with no gaps
  KOA012  `@dataclass` is `kw_only=True` so fields can't be passed positionally
  KOA013  every function/method/nested function has a docstring

Run: `uv run python -m tools.repolint [paths...]` (defaults to `src/` and `tests/`).
Pass `--fix` to auto-apply the safe textual fixes (KOA001, KOA004).
"""

import argparse
import ast
import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATHS = ["src/", "tests/"]
LINT_SUFFIXES = (".py", ".md")
DOUBLE_BACKTICK = "`" * 2
FUTURE_ANNOTATIONS = "from __future__ import annotations"
PYPROJECT = REPO_ROOT / "pyproject.toml"
MY_PREFIX_RE = re.compile(r"\bmy[_-]|\bMy[A-Z]")
ADR_DIR = REPO_ROOT / "docs" / "adr"
ADR_NAME_RE = re.compile(r"^(\d{4})-.*\.md$")


def _load_exempt_modules() -> frozenset[str]:
    """Read ruff's `flake8-type-checking.exempt-modules` from `pyproject.toml`.

    Ruff exempts these from TYPE_CHECKING moves, so they belong at runtime;
    KOA008 flags any that appear under `if TYPE_CHECKING:`. Falls back to an
    empty set if the config (or key) is missing so the check stays a no-op
    rather than crashing when run outside the repo.
    """
    try:
        with PYPROJECT.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError:
        return frozenset()
    section = data.get("tool", {}).get("ruff", {}).get("lint", {})
    modules = section.get("flake8-type-checking", {}).get("exempt-modules", [])
    return frozenset(modules)


EXEMPT_MODULES = _load_exempt_modules()


@dataclass(frozen=True, kw_only=True)
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


def _line_col_of(source: str, pos: int) -> tuple[int, int]:
    """Return the 1-indexed (line, col) of `pos` within `source`."""
    line = source.count("\n", 0, pos) + 1
    col = pos - source.rfind("\n", 0, pos)
    return line, col


def _check_future_import(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag `from __future__ import annotations` (KOA001)."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
        ):
            yield Violation(
                path=path,
                line=node.lineno,
                col=node.col_offset + 1,
                code="KOA001",
                message="remove `from __future__ import annotations`",
            )


def _check_strict_model(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag a model inheriting `BaseModel` directly (KOA002)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name in {
            "FrozenModel",
            "StrictModel",
        }:
            continue
        if any(_is_named(base, "BaseModel") for base in node.bases):
            yield Violation(
                path=path,
                line=node.lineno,
                col=node.col_offset + 1,
                code="KOA002",
                message=f"`{node.name}` must subclass `StrictModel` or `FrozenModel`,"
                " not `BaseModel`",
            )


def _check_protocol_ellipsis(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag `...` bodies in Protocol methods (KOA003)."""
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
    """Yield a KOA003 for each `...` statement in one Protocol method."""
    for stmt in method.body:
        if (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is Ellipsis
        ):
            yield Violation(
                path=path,
                line=stmt.lineno,
                col=stmt.col_offset + 1,
                code="KOA003",
                message="drop `...` from the Protocol method; the docstring is enough",
            )


def _check_double_backticks(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag double backticks in docstrings (KOA004)."""
    for node in ast.walk(tree):
        doc = _docstring_node(node)
        if doc is None or not isinstance(doc.value, str):
            continue
        if DOUBLE_BACKTICK in doc.value:
            yield Violation(
                path=path,
                line=doc.lineno,
                col=doc.col_offset + 1,
                code="KOA004",
                message="use single backticks in docstrings, not double",
            )


def _check_homogeneous_tuple(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag `tuple[T, ...]` annotations (KOA005)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript) or not _is_named(node.value, "tuple"):
            continue
        sliced = node.slice
        if isinstance(sliced, ast.Tuple) and any(
            isinstance(elt, ast.Constant) and elt.value is Ellipsis
            for elt in sliced.elts
        ):
            yield Violation(
                path=path,
                line=node.lineno,
                col=node.col_offset + 1,
                code="KOA005",
                message="use `list[T]` for homogeneous sequences, not `tuple[T, ...]`",
            )


def _check_self_forward_ref(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag a string forward-ref return to the enclosing class (KOA006)."""
    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            returns = method.returns
            if isinstance(returns, ast.Constant) and returns.value == cls.name:
                yield Violation(
                    path=path,
                    line=returns.lineno,
                    col=returns.col_offset + 1,
                    code="KOA006",
                    message=f'return `Self`, not the forward-ref `"{cls.name}"`',
                )


def _check_exempt_in_type_checking(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag a ruff-exempt module imported under `TYPE_CHECKING` (KOA008)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if not isinstance(node.test, ast.Name) or node.test.id != "TYPE_CHECKING":
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.ImportFrom) and stmt.module in EXEMPT_MODULES:
                yield Violation(
                    path=path,
                    line=stmt.lineno,
                    col=stmt.col_offset + 1,
                    code="KOA008",
                    message=(
                        f"move `{stmt.module}` out of TYPE_CHECKING; ruff exempts it"
                    ),
                )


MAX_POSITIONAL_ARGS = 3


def _check_positional_args(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag functions with more than 3 positional parameters (KOA009)."""
    class_parents: dict[int, type[ast.AST]] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            class_parents[id(child)] = type(parent)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name.startswith("test_"):
            continue
        positional = node.args.args
        if class_parents.get(id(node)) is ast.ClassDef:
            positional = positional[1:]
        if len(positional) > MAX_POSITIONAL_ARGS:
            yield Violation(
                path=path,
                line=node.lineno,
                col=node.col_offset + 1,
                code="KOA009",
                message=f"too many positional args ({len(positional)}"
                f" > {MAX_POSITIONAL_ARGS}); use * to make some keyword-only",
            )


def _has_kw_only_true(keywords: list[ast.keyword]) -> bool:
    """Report whether `kw_only=True` appears among the decorator keywords."""
    return any(
        kw.arg == "kw_only"
        and isinstance(kw.value, ast.Constant)
        and kw.value.value is True
        for kw in keywords
    )


def _check_dataclass_kw_only(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag a `@dataclass` that isn't `kw_only=True` (KOA012)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not _is_named(target, "dataclass"):
                continue
            keywords = decorator.keywords if isinstance(decorator, ast.Call) else []
            if not _has_kw_only_true(keywords):
                yield Violation(
                    path=path,
                    line=node.lineno,
                    col=node.col_offset + 1,
                    code="KOA012",
                    message=(
                        "decorate `@dataclass(kw_only=True)` so fields"
                        " can't be passed positionally"
                    ),
                )


def _check_missing_docstring(tree: ast.Module, path: Path) -> Iterator[Violation]:
    """Flag any function/method/nested function lacking a docstring (KOA013)."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and ast.get_docstring(node) is None
        ):
            yield Violation(
                path=path,
                line=node.lineno,
                col=node.col_offset + 1,
                code="KOA013",
                message=f"add a one-line docstring to `{node.name}`",
            )


CHECKS = (
    _check_future_import,
    _check_strict_model,
    _check_protocol_ellipsis,
    _check_double_backticks,
    _check_homogeneous_tuple,
    _check_self_forward_ref,
    _check_exempt_in_type_checking,
    _check_positional_args,
    _check_dataclass_kw_only,
    _check_missing_docstring,
)


def check_source(source: str, path: Path) -> list[Violation]:
    """Return every convention violation in source (parsed from path)."""
    tree = ast.parse(source, filename=str(path))
    return [v for check in CHECKS for v in check(tree, path)]


def _check_possessive_prefix(source: str, path: Path) -> Iterator[Violation]:
    """Flag a possessive `my` prefix anywhere in the text (KOA007)."""
    for match in MY_PREFIX_RE.finditer(source):
        line, col = _line_col_of(source, match.start())
        yield Violation(
            path=path,
            line=line,
            col=col,
            code="KOA007",
            message="drop the possessive `my` prefix; it models bad names for users",
        )


TEXT_CHECKS = (_check_possessive_prefix,)


def check_text(source: str, path: Path) -> list[Violation]:
    """Return every text-level convention violation in source (any file type)."""
    return [v for check in TEXT_CHECKS for v in check(source, path)]


def _check_duplicate_prefixes(
    numbered: list[tuple[int, Path]],
) -> Iterator[Violation]:
    """Yield a KOA010 for each ADR file sharing a number with another."""
    counts = Counter(number for number, _ in numbered)
    for number, path in numbered:
        if counts[number] > 1:
            yield Violation(
                path=path,
                line=1,
                col=1,
                code="KOA010",
                message=f"duplicate ADR number {number:04d};"
                " each ADR file needs a unique numeric prefix",
            )


def _check_consecutive_numbering(
    numbered: list[tuple[int, Path]],
    adr_dir: Path,
) -> Iterator[Violation]:
    """Yield a KOA011 when ADR numbers aren't a gapless run from `0001`."""
    present = sorted({number for number, _ in numbered})
    if not present:
        return
    expected = list(range(1, len(present) + 1))
    if present != expected:
        got = ", ".join(f"{number:04d}" for number in present)
        yield Violation(
            path=adr_dir,
            line=1,
            col=1,
            code="KOA011",
            message=f"ADR numbers must be consecutive from 0001 with no gaps;"
            f" got {got}, expected 0001\N{EN DASH}{len(present):04d}",
        )


def check_adr_numbering(adr_dir: Path) -> list[Violation]:
    """Return ADR-directory numbering violations (KOA010, KOA011).

    Scans adr_dir for `NNNN-*.md` files and checks that their numeric
    prefixes are unique (KOA010) and form a consecutive run from `0001`
    (KOA011) — the sequential convention from `docs/agents/domain.md`.
    """
    numbered = [
        (int(match.group(1)), path)
        for path in sorted(adr_dir.glob("*.md"))
        if (match := ADR_NAME_RE.match(path.name))
    ]
    return [
        *_check_duplicate_prefixes(numbered),
        *_check_consecutive_numbering(numbered, adr_dir),
    ]


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


def iter_files(paths: list[str]) -> Iterator[Path]:
    """Yield every `.py` or `.md` file under the given paths (files or directories)."""
    for raw in paths:
        root = Path(raw)
        if root.is_file():
            yield root
        else:
            yield from sorted(p for pat in ("*.py", "*.md") for p in root.rglob(pat))


def main(argv: list[str] | None = None) -> int:
    """Lint the given paths; return 1 if any violations remain."""
    parser = argparse.ArgumentParser(description="Repo-specific convention checks.")
    parser.add_argument("paths", nargs="*", default=list(DEFAULT_PATHS))
    parser.add_argument("--fix", action="store_true", help="apply safe textual fixes")
    args = parser.parse_args(argv)

    violations: list[Violation] = []
    for file in iter_files(args.paths or list(DEFAULT_PATHS)):
        source = file.read_text(encoding="utf-8")
        if file.suffix == ".py":
            if args.fix:
                fixed = fix_source(source)
                if fixed != source:
                    file.write_text(fixed, encoding="utf-8")
                    source = fixed
            violations.extend(check_source(source, file))
        violations.extend(check_text(source, file))

    if ADR_DIR.is_dir():
        violations.extend(check_adr_numbering(ADR_DIR))

    for violation in violations:
        sys.stdout.write(violation.render() + "\n")
    if violations:
        sys.stdout.write(f"\nFound {len(violations)} convention violation(s).\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
