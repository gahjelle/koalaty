# The manual feed: `start`/`harvest` adapter seam and driver-by-feed

The manual feed (`start` → pending run → `harvest`) is uniform across harnesses, and a run's `driver` is derived from the feed that produced it, not from a task/harness formula.

## The adapter seam

`start` never invokes a harness — that is the whole point of the manual feed (a human drives the session). But `start` is *not* adapter-free: setup is a harness-specific quirk (Claude Code selects a model with `/model`, opencode with `/models`; each tells you how to find a finished session's id differently), and hiding harness quirks is the adapter's job. So the adapter grows a third capability:

- `start(task, model) -> instructions` — **base protocol, required.** Returns the harness-tailored manual setup instructions, *including how to obtain the session id to harvest with*. Every harness is manually drivable, including ones with no headless mode, so this lives on the base `Adapter`, not on `InvocableAdapter`.
- `harvest(session_id) -> HarvestedSession` — base, required (unchanged).
- `invoke(task, model) -> session_id` — optional `InvocableAdapter` (unchanged).

The session id is **always supplied externally** at `harvest` time — the harness mints it while the human drives, so it cannot be known at `start`. This makes the two-step shape (`start` prints instructions; `harvest` takes an external id) identical across harnesses; only the instruction *text* varies. The fake adapter is a faithful stand-in: its `start` instructions hand you a concrete id ("…run `koalaty harvest <run-id> --session abc123`") because it is self-contained, and its `harvest` resolves any id deterministically. `task`/`model`/`turns` come from `pending.json`, so the harvested session need not carry them.

## Driver by feed

`driver` is derived from the feed that produced the run: the manual feed (`start`/`harvest`) always records `human`; the automated feed (`run`) always records `koalaty`. This supersedes reading the CONTEXT.md formula as "compute `driver` from `interactive`/headless-capability." That formula is reframed as a **routing** rule — which feeds a task *may* use (`interactive` or no-headless ⇒ manual-only) — separate from who actually drove. A human may choose the manual feed for an otherwise-automatable task, and `driver` then honestly records `human`.

## Consequences

- `runs.py` gains `start_run` (mint id → `adapter.start` → write `pending.json`, `driver="human"`) and `harvest_run` (load pending → `adapter.harvest` → assemble `Result` → write/remove), mirroring `run_automated`'s literal `driver="koalaty"` (ADR-0005).
- `derive_driver` becomes a routing predicate (may this task be automated?), not the source of the recorded `driver`.
- Real `claudecode.start()`/`harvest()` arrive with the Claude Code adapter (a later slice); the fake proves the seam now.
