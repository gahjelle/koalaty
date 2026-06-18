default: check

check: fmt-check lint typecheck test

fmt:
    @uv run ruff format

fmt-check:
    @uv run ruff format --check

lint:
    @uv run ruff check

typecheck:
    @uv run ty check

test:
    @uv run pytest -q

fix:
    @uv run ruff check --fix
    @uv run ruff format
