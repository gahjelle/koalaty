# Koalaty — High-Level Plan

> **Koalaty** — *Koalaty Control.* Evaluate and compare models across agent harnesses.
> High-level only. Vocabulary lives in [`CONTEXT.md`](../CONTEXT.md); load-bearing decisions in [`docs/adr/`](./adr/). Schemas, flags, and scoring weights are for later sessions.

## Goal

Evaluate and compare **models** running inside **agent harnesses** on a shared set of **tasks**, and store every outcome in one uniform, queryable place so combos can be compared after the fact. Both *automated* and *manual* evaluations are first-class and produce the same record.

- **Harnesses (initial):** Claude Code (primary — drives the manual feed today), Copilot CLI, Codex CLI, opencode. Extensible.
- **Models:** Claude, GPT, etc. — chosen per run.

## Center of gravity: the pouch

Koalaty's product is the **pouch** — the results store. Everything else exists to fill or query it. Results enter via **two equal feeds** (see [ADR-0001](./adr/0001-pouch-is-the-product-two-feeds.md)):

- **Automated run** — koalaty *invokes* a harness headlessly, then *harvests* the session. `driver = koalaty`.
- **Manual run** — a human drives the harness; koalaty *harvests* the session afterward by its ID and runs a **survey**. `driver = human`.

The shared capability is **harvest** (read a finished session by ID and normalize it). `driver` is **derived**, not chosen: `human` if the task is `interactive` or the harness has no headless mode, else `koalaty`.

## The two workflows

**Automated** (one command):
```
koalaty run <task> --harness H --model M     # invoke → harvest → store
```

**Manual** (async, with an explicit pending state):
```
koalaty start <task> --harness H --model M   # prints prompt + setup, registers a PENDING run, returns run ID
#   ...you drive the session by hand until the task's done-condition is met...
koalaty harvest <run-id> --session <sid>     # harvest the session into the run, run the survey → complete result
```

**Grade & query** (over the pouch, re-runnable, never touches a harness):
```
koalaty paws [filter]      # grading pass: mechanical + rubric
koalaty compare [filter]   # the comparison report
```

**Authoring:**
```
koalaty task new <id> [--from-example <name>]   # scaffold a task directory
```

## Components

### 1. Tasks (authored, version-controlled)

A **task** is the bundle koalaty owns and holds fixed across models. Plain files, hand-editable, scaffolded by `task new`. Config in TOML, prose in Markdown:

```
tasks/<id>/
  task.toml      # turns (one-shot|scripted|interactive), tags (drop-bear…), [gum] pointer
  prompt.md      # the prompt text to paste/send; for scripted, turns are split on bare `---` lines
  done.md        # prose stopping-guidance (matters most for interactive)
  gum/           # starting fixture: inline files, or pointer to git URL + pinned commit
  tests/         # mechanical eval assets
  rubric.md      # rubric criteria
```

Required files are `task.toml` + `prompt.md`; the rest are optional (absent ⇒
empty/none). A `scripted` prompt splits into its ordered turn list on lines that
are exactly `---`; `one-shot`/`interactive` keep the whole file as one literal
prompt. There is no `turns.md`.

- **`turns`** sets turn structure and (with harness capability) determines the driver: `one-shot`/`scripted` → automated; `interactive` → manual-only.
- **drop-bear** is a task tag (adversarial). **Example tasks** ship in-package and are copied into `tasks/` — they are real tasks, not joeys.

### 2. Adapters (one per harness)

Hide harness-specific quirks. Two methods:

- **`harvest(session_id)` — required.** Locate a finished session in the harness's local storage and normalize it. **Harvest normalization is the hard part** (each harness stores sessions differently; pin CLI versions).
- **`invoke(task, gum, model)` — optional.** Headlessly drive the harness, return a session ID, hand off to `harvest`. Absent ⇒ harness is manual-only.

So `run = invoke + harvest`; manual `start`/`harvest` = `harvest` alone.

### 3. The pouch (storage)

Files-first; the query index is derived and disposable (see [ADR-0002](./adr/0002-files-source-of-truth-derived-index.md)):

- One **directory per run**, keyed by a self-describing **run ID** (`<task>-<harness>-<model>-<date>-<shortid>`; see [ADR-0003](./adr/0003-run-id-ordering-and-canonical-names.md)). Holds raw harvested artifacts + normalized **`result.json`** (the source of truth).
- A **pending run** exists between `start` and `harvest`.
- The **index** (SQLite/DuckDB) is rebuilt from `result.json` files — never authoritative, not git-tracked.
- The pouch is a separate, configurable location (koalaty is the tool; the pouch is the user's data).
- Every `result.json` carries reproducibility metadata: harness + CLI version, model + version, date, gum commit.

### 4. Evaluation: three inputs

| Input          | Measures                                                  | Producer                                       | When       | Applies to       |
| -------------- | --------------------------------------------------------- | ---------------------------------------------- | ---------- | ---------------- |
| **mechanical** | objective facts (patch applies, build/tests/lint)         | derived from artifacts                         | paws       | all runs         |
| **rubric**     | quality of output/transcript vs shared criteria           | LLM-judge and/or human reviewer (third-person) | paws       | all runs         |
| **survey**     | first-person *driver experience* (friction, hand-holding) | the human driver                               | at harvest | manual runs only |

- **paws** is the later, re-runnable grading pass (mechanical + rubric). **survey** rides with the run at harvest, separate from paws.
- Rubric stores judge and human scores side by side to assess agreement. (If the reviewer is the driver, blinding is lost — handle when designing paws.)

### 5. Compare

- Comparison unit: **(model × harness) per task**.
- **Repeated runs are first-class** and aggregated; variance matters (one run is an anecdote).
- Each cell surfaces mechanical pass-rate, rubric (judge vs human), survey aggregates (manual cells), and cost/tokens/wallclock.
- Defaults: exclude **joeys**; optional slices by tag (e.g. drop-bear) or driver.

## Design keystone

The **`result.json` schema** is the linchpin. If every adapter harvests into the same shape and every task declares its eval method, cross-model / cross-harness comparison becomes a query — regardless of which feed produced the result.

## Open questions (resolve in later sessions)

- Exact `result.json` schema fields and types.
- Survey question set; rubric design + LLM-judge prompt; calibration against humans; blinding.
- Cost/token normalization across providers.
- Index query layer: SQLite vs DuckDB; report shapes for `compare`.
- Per-harness harvest normalization details + CLI version pinning / auto-update handling.
- Sandboxing strategy for pre-authorized (`--allow-all-tools`-style) automated runs.

## Suggested build order (manual-first)

1. Define the `result.json` schema.
2. Pouch storage: write/read run directories; rebuild the index.
3. First adapter **harvest** end-to-end (Claude Code) + the **manual feed**: `start` → pending run → `harvest` + survey. *(Proves "the pouch is the product" with your real daily workflow.)*
4. Mechanical **paws**.
5. Add **invoke** to that adapter → **automated** `run`.
6. Second adapter (Copilot CLI) to validate the abstraction.
7. Rubric **paws** (judge + human, side by side).
8. **compare** report.
