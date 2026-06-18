# Quality gates

`just check` is the **definition of done** for every slice. It runs four gates in order, stopping on the first failure:

1. `just fmt-check` — `uv run ruff format --check`
2. `just lint` — `uv run ruff check`
3. `just conventions` — `uv run python -m tools.repolint` (repo-specific `KOA` rules ruff/ty can't express; see [code-conventions.md](./code-conventions.md#repo-conventions-repolint))
4. `just typecheck` — `uv run ty check` (covers `src/` and `tests/`)
5. `just test` — `uv run pytest -q`

A slice is not done until `just check` is green. CI mirrors these exact commands on every push and pull request, so a green CI means the same gate passed remotely.

Justfile recipes echo their commands (no `@` prefix) so each gate prints the exact tool invocation it runs — less silent, but makes failures in CI logs immediately traceable to the failing command.

## Quick fixes

- Auto-format: `just fmt`
- Lint fix: `just fix` (runs `ruff check --fix` then `ruff format`)
- Convention fix: `uv run python -m tools.repolint --fix` (safe textual fixes for KOA001 and KOA004 only)

## Pre-commit hooks

Run `uv run prek install` once after cloning to wire up git pre-commit hooks. The hooks run ruff lint, ruff format, and ty on every commit — catching failures before they reach CI.
