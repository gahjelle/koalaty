# Pending runs are a separate `pending.json`, not a status field

A manual run is **pending** between `start` and `harvest` (CONTEXT.md). We store that state as its own `pending.json` inside the run directory; `harvest` writes `result.json` and removes `pending.json`. A `result.json` therefore always means a completed run, and a pending run never masquerades as one.

```
pouch/<run-id>/
  pending.json   # exists only between start and harvest
  result.json    # written at harvest; pending.json removed
  raw/session.json
```

## Considered Options

- **Separate `pending.json` (chosen).** `read_results()` keeps globbing `*/result.json`, so pending runs are *structurally* invisible to `compare` and the derived index with no extra filtering — the acceptance criterion "distinguishable from a completed result" falls out for free. A `PendingRun` schema carries only what `start` knows (run id, task, harness, model, `driver`, `turns`, `tags`, `joey`, created-at); `Result` stays free of harvest-derived `Optional`s.
- **One `result.json` with a `status: pending | complete` field.** Rejected: every reader of the pouch (`compare`, future index) would have to filter by status, and `Result` would carry `started_at`/`finished_at`/`outcome`/`summary`/`survey` as nullable-until-harvest fields, blurring the "a result is a completed, comparable record" invariant.
- **A separate `pouch/pending/` area.** Rejected: harvest would have to move directories, and run-id pathing would fork by state.

## Consequences

- A pending run and a completed run share the same run-id directory; `harvest` is an in-place completion (write `result.json`, delete `pending.json`).
- `harvest` on a run id with no `pending.json` (unknown, or already harvested) is an error that writes nothing.
- This is the pouch's on-disk contract (the pouch is the product, ADR-0001; files are the source of truth, ADR-0002), so it is deliberately recorded here.
