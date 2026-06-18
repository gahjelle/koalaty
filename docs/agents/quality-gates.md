# Quality gates

`just check` is the **definition of done** for every slice. It runs four gates in order, stopping on the first failure:

1. `just fmt-check` — `uv run ruff format --check`
2. `just lint` — `uv run ruff check`
3. `just typecheck` — `uv run ty check` (covers `src/` and `tests/`)
4. `just test` — `uv run pytest -q`

A slice is not done until `just check` is green. CI mirrors these exact commands on every push and pull request, so a green CI means the same gate passed remotely.

## Quick fixes

- Auto-format: `just fmt`
- Lint fix: `just fix` (runs `ruff check --fix` then `ruff format`)

## Pre-commit hooks

Run `uv run prek install` once after cloning to wire up git pre-commit hooks. The hooks run ruff lint, ruff format, and ty on every commit — catching failures before they reach CI.
