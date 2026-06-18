# Testing

## Approach

Work test-first: defer to the `tdd` skill for the red → green → refactor loop. Write a failing test before any implementation, then make it pass with the minimum code needed.

## What to test

- Assert **external behavior via the CLI** — invoke `main()` or test CLI commands end-to-end.
- Do not test internal implementation details; test observable outcomes.

## The fake adapter

The `fake` adapter (`adapters/fake.py`) is the injected seam for tests. Use it instead of real model APIs to keep tests fast and hermetic. Never mock the filesystem.

## Boundaries

- `tmp_path` (pytest's built-in fixture) is the only real filesystem boundary allowed in tests.
- No network calls in tests — use the fake adapter.
- No mocking of the filesystem — use `tmp_path` for real file I/O.

## Test layout

Tests live in `tests/`. Pytest is configured with `testpaths = ["tests"]` and the src layout (`src/` on the path via uv). Test files follow the `test_<module>.py` convention.
