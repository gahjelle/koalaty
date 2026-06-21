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

# Set up tasks and run a few of them
setup:
    rm -rf tasks/
    uv run koalaty task new --from-example wombat
    uv run koalaty task new --from-example quokka
    uv run koalaty task new bilby
    uv run koalaty run wombat --harness fake --model faiku
    uv run koalaty run wombat --harness fake --model faiku
    uv run koalaty run quokka --harness fake --model faiku
    uv run koalaty run bilby --harness fake --model faiku
    uv run koalaty run wombat --harness fake --model fonnet
    uv run koalaty run bilby --harness fake --model fonnet
    uv run koalaty run bilby --harness fake --model fonnet
    uv run koalaty compare
