# Code conventions

## Environment

- Python 3.14, managed by **uv**.
- Install deps: `uv sync`. Run tools: `uv run <tool>`.
- Source layout: `src/koalaty/` for application code, `tests/` for tests.

## Linting and formatting

- **ruff** with `select = ["ALL"]` and ignores `COM812`, `D203`, `D213`.
- Per-file test ignores: `S101`, `PLR2004`, `SLF001`, `INP001`.
- Every public module, class, and function **must have a docstring** (ruff `D` rules enforce this).
- Full **type annotations** are required on all public APIs (ruff `ANN` rules enforce this).
- Never blanket-ignore the linter with `# noqa` — fix the issue or use a targeted `# noqa: CODE` with a comment explaining why.

## Style

- Prefer `pathlib` over `os.path` for filesystem operations.
- Thin `cli/` layer — application logic lives in domain modules, not in CLI handlers.
- Adapters live in `adapters/` and follow the interface defined in `adapters/base.py`.

## Module structure

```
src/koalaty/
  __init__.py        # package docstring only
  __main__.py        # main() entry point for cyclopts app
  cli/               # CLI definitions; no business logic
  config.py          # configuration loading and validation
  result.py          # result types (Pydantic models)
  pouch.py           # pouch read/write operations
  compare.py         # comparison logic
  adapters/          # adapter protocol + implementations
```

## Domain vocabulary

Vocabulary comes from `CONTEXT.md`. Do not invent synonyms. If you introduce a genuinely new domain term, update `CONTEXT.md` first.
