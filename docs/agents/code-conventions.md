# Code conventions

## Environment

- Python 3.14, managed by **uv**.
- Install deps: `uv sync`. Run tools: `uv run <tool>`.
- Source layout: `src/koalaty/` for application code, `src/tools/` for repo dev tooling (e.g. the convention linter), `tests/` for tests.

## Linting and formatting

- **ruff** with `select = ["ALL"]` and ignores `COM812`, `D203`, `D213`.
- Per-file test ignores: `S101`, `PLR2004`, `SLF001`, `INP001`.
- Every public module, class, and function **must have a docstring** (ruff `D` rules enforce this). Functions and methods go further — *every* one needs at least a one-line docstring, including `_`-prefixed and nested functions that ruff's `D` rules leave alone (enforced by KOA013 below).
- Full **type annotations** are required on all public APIs (ruff `ANN` rules enforce this).
- Never blanket-ignore the linter with `# noqa` — fix the issue or use a targeted `# noqa: CODE` with a comment explaining why.
- For intentional Unicode characters that trigger RUF001 (ambiguous characters), use `\N{name}` escapes (e.g., `\N{EN DASH}`) instead of the literal character or `\u` escapes. This is self-documenting and avoids the noqa entirely.

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
- **KOA002 — Pydantic models inherit `FrozenModel`/`StrictModel`, never `BaseModel` directly.**
  These are thin project bases (`koalaty.schemas`) — `BaseModel` subclasses that
  forbid extra fields — and are the only classes allowed to subclass `BaseModel`.
  Inherit `FrozenModel` for immutable models, `StrictModel` for mutable ones.
- **KOA003 — `Protocol` methods omit the `...` body.** The docstring is body
  enough; drop the trailing `...`.
- **KOA004 — docstrings use single backticks, never double.** Write `` `code` ``,
  not ` ``code`` ` (the linter's `--fix` collapses these automatically).
- **KOA005 — homogeneous sequences use `list[T]`, not `tuple[T, ...]`.**
- **KOA006 — return `Self`, never a string forward-ref to the enclosing class.**
  Import `Self` from `typing` and annotate `-> Self` instead of `-> "Thing"`.
- **KOA007 — no possessive `my` prefix in code or docs.** An identifier or token
  beginning with `my` followed by `_` or `-`, or `My` followed by an uppercase
  letter, models bad naming and leaks into examples shown to users. Pick a name
  that describes the thing instead. Checked as text across `.py` and `.md` files.
- **KOA008 — ruff-exempt modules stay at runtime, not in `TYPE_CHECKING`.**
  `pathlib`, `datetime`, and `typing` are listed in
  `[tool.ruff.lint.flake8-type-checking] exempt-modules` in `pyproject.toml`, so
  ruff will never move them into a `TYPE_CHECKING` block. Keep their imports at
  module top level; do not nest them under `if TYPE_CHECKING:`.
- **KOA009 — at most 3 positional parameters.** Functions with many positional
  args are hard to call correctly. Beyond 3, make parameters keyword-only
  (after a bare `*` separator). `self`/`cls` in methods don't count toward
  the limit. Use a bare `*` separator to make additional parameters keyword-only.
- **KOA010 — no duplicate numeric prefixes in `docs/adr/`.** Two ADR files must
  not share the same `NNNN-` prefix. Parallel branches each adding "the next"
  ADR collide on a number; this catches it at `just check` time, before merge.
  Renumber one of the colliders so every ADR prefix is unique.
- **KOA011 — ADR numbers are consecutive from `0001`.** The prefixes in
  `docs/adr/` must form `0001, 0002, …, N` with no gaps and no zero. A gap
  suggests a deleted or missing ADR; a non-1-based start suggests a truncation.
  Both are drift from the sequential convention in
  [domain.md](./domain.md). Unlike the other rules, KOA010/KOA011 scan the
  `docs/adr/` directory rather than the files passed on the command line.
- **KOA012 — `@dataclass` must pass `kw_only=True`.** Stdlib dataclasses
  otherwise accept fields positionally, so a multi-field value object gets
  built as `Thing(a, b, c, …)` — the same hard-to-read positional soup KOA009
  guards against at the definition. Making the dataclass `kw_only` forces every
  call site to name its fields, and `ty` flags any positional construction for
  free. (Pydantic `FrozenModel`/`StrictModel` already reject positional args,
  so KOA002's models need nothing extra; this rule covers the stdlib
  `@dataclass` that KOA002 doesn't.)
- **KOA013 — every function/method has a docstring.** At least a one-line
  docstring on *every* `def`/`async def`, including `_`-prefixed helpers and
  nested functions. ruff's pydocstyle `D` rules only require docstrings on
  *public* names, so private and nested functions slip through; KOA013 closes
  that gap. The name plus a behavioral one-liner keeps even tiny helpers
  self-explanatory.

## Style

- Prefer `pathlib` over `os.path` for filesystem operations.
- Thin `cli/` layer — application logic lives in domain modules, not in CLI handlers (see [ADR-0006](../adr/0006-runs-module-for-orchestration.md)).
- Adapters live in `adapters/` and follow the interface defined in `adapters/base.py`.
- Avoid underscore-prefixed names for "private" symbols — the visual noise outweighs the benefit. Control the public API with `__all__` when a module needs to distinguish exported names from internal helpers.

## Domain vocabulary

Vocabulary comes from `CONTEXT.md`. Do not invent synonyms. If you introduce a genuinely new domain term, update `CONTEXT.md` first.
