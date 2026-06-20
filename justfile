default: check

# Run all quality gates in order, stopping on the first failure.
check: fmt-check lint conventions typecheck test

# Auto-format the codebase with ruff.
fmt:
    uv run ruff format -q

# Check formatting without writing changes.
fmt-check:
    uv run ruff format --check -q

# Lint the codebase with ruff.
lint:
    uv run ruff check -q

# Type-check src/ and tests/ with ty.
typecheck:
    uv run ty check -q

# Enforce repo-specific conventions ruff/ty can't express.
conventions *args:
    uv run python -m tools.repolint {{args}}

# Run the test suite quietly.
test *args:
    uv run pytest -q {{args}}

# Auto-fix lint issues then reformat.
fix:
    uv run ruff check --fix -q
    uv run python -m tools.repolint --fix
    uv run ruff format -q
