# Code conventions

## Environment

- Python 3.14, managed by **uv**.
- Install deps: `uv sync`. Run tools: `uv run <tool>`.
- Source layout: `src/koalaty/` for application code, `src/tools/` for repo dev tooling (e.g. the convention linter), `tests/` for tests.

## Linting and formatting

- **ruff** with `select = ["ALL"]` and ignores `COM812`, `D203`, `D213`.
- Per-file test ignores: `S101`, `PLR2004`, `SLF001`, `INP001`.
- Every public module, class, and function **must have a docstring** (ruff `D` rules enforce this).
- Full **type annotations** are required on all public APIs (ruff `ANN` rules enforce this).
- Never blanket-ignore the linter with `# noqa` — fix the issue or use a targeted `# noqa: CODE` with a comment explaining why.

## Repo conventions (`repolint`)

Some conventions can't be expressed in ruff or ty, so they live in a small
in-repo linter, `src/tools/repolint.py` (the `tools` package sits beside
`koalaty` under `src/` so it imports without any path juggling), wired into
`just check` (the `conventions` gate). It runs over `src/` and `tests/` and
reports `KOA` codes. Run it directly with `uv run python -m tools.repolint
[paths...]`; `--fix` applies the safe textual fixes (KOA001 and KOA004). Each
rule and how to satisfy it:

- **KOA001 — no `from __future__ import annotations`.** Python 3.14 evaluates
  annotations lazily (PEP 649), so the import is dead weight. Delete it; quote
  any annotation that genuinely needs deferring, or guard the import under
  `if TYPE_CHECKING:`.
- **KOA002 — Pydantic models inherit `FrozenModel`, never `BaseModel` directly.**
  `FrozenModel` (`koalaty.schemas`) is a thin project base — a
  `pydantic.BaseModel` that forbids extra fields and freezes instances — and is
  the one class allowed to subclass `BaseModel`. Inherit it for every model.
- **KOA003 — `Protocol` methods omit the `...` body.** The docstring is body
  enough; drop the trailing `...`.
- **KOA004 — docstrings use single backticks, never double.** Write `` `code` ``,
  not ` ``code`` ` (the linter's `--fix` collapses these automatically).
- **KOA005 — homogeneous sequences use `list[T]`, not `tuple[T, ...]`.**
- **KOA006 — return `Self`, never a string forward-ref to the enclosing class.**
  Import `Self` from `typing` and annotate `-> Self` instead of `-> "Thing"`.

## Style

- Prefer `pathlib` over `os.path` for filesystem operations.
- Thin `cli/` layer — application logic lives in domain modules, not in CLI handlers (see [ADR-0005](../adr/0005-runs-module-for-orchestration.md)).
- Adapters live in `adapters/` and follow the interface defined in `adapters/base.py`.
- Avoid underscore-prefixed names for "private" symbols — the visual noise outweighs the benefit. Control the public API with `__all__` when a module needs to distinguish exported names from internal helpers.

## Domain vocabulary

Vocabulary comes from `CONTEXT.md`. Do not invent synonyms. If you introduce a genuinely new domain term, update `CONTEXT.md` first.
