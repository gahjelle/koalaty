# Runs module for run orchestration

Run orchestration (validate → invoke → harvest → assemble → write) lives in a dedicated `runs` module, not in the CLI. The CLI handlers are thin wrappers that parse input and call domain functions.

```
runs.py              # run_automated(), future start()/harvest()
cli/main.py          # CLI definitions only; delegates to runs + other modules
```

We chose this over keeping orchestration in the CLI (the status quo) for two reasons. First, any alternative frontend — an API, a GUI — would need the same pipeline. Embedding it in the CLI forces every frontend to duplicate the sequence or depend on the CLI layer. Second, the validation guards (unknown harness, non-invocable adapter, interactive task rejection) are preconditions of an *automated run*, not of the CLI — they belong with the domain function that enforces them.

The module is named `runs` (not `orchestrator` or `runner`) because it houses all run workflows: `run_automated` today, `start` and `harvest` for manual runs later. Both workflows share the same harvest → assemble → write suffix, which is a private helper inside the module. Splitting automated and manual runs into separate modules would duplicate that suffix or require a third shared module — one module keeps the shared logic local.

`run_automated` accepts a loaded `Task` object (not a task-id string plus tasks directory) because task loading is already a distinct concern in `tasks.py`. An optional `now` parameter accepts a `datetime` for deterministic testing. The driver is the literal string `"koalaty"` rather than a call to `derive_driver`, since an automated run is always self-driven.

## Consequences

- The CLI `run()` handler is three lines: load task, call `run_automated`, return run id.
- CLI-level input validation (model name format, harness name format) stays in the CLI because it is about translating user input, not about domain preconditions.
- Adding a new frontend requires only calling `run_automated` — no orchestration to duplicate.
- Adding manual runs means adding `start()` and `harvest()` to `runs.py`, sharing the private harvest-assemble-write helper.
