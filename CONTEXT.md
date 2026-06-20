# Koalaty

Koalaty evaluates and compares **models** running inside **agent harnesses** on a shared set of tasks. Its center of gravity is the results store (the *pouch*): both automated and manual evaluations feed the same store so they can be compared side by side. Marsupial theme supplies the feature vocabulary.

## Language

**pouch**:
The results store — the canonical home for every recorded result. Koalaty's product; everything else exists to fill or query it. A separate, configurable location of plain files (one directory per run, source of truth), not coupled to koalaty's source tree.
_Avoid_: database, store, results dir

**index**:
A derived, disposable query database (SQLite/DuckDB) rebuilt from the pouch's `result.json` files. Never the source of truth; not git-tracked.
_Avoid_: db, cache, store

**harness**:
An agent CLI/tool that drives a model through a session (e.g. Claude Code, Copilot CLI, Codex CLI, opencode). Koalaty compares across harnesses.
_Avoid_: tool, agent, CLI

**adapter**:
The per-harness implementation that hides harness-specific quirks. Exposes `start` (required — returns the harness-tailored manual setup instructions, including how to obtain the **session** id to **harvest** with) and `harvest` (required), plus `invoke` (optional; absent ⇒ harness is manual-only, but `start`/`harvest` still work). The manual feed is uniform across harnesses — only the `start` instruction text differs. The hard part is **harvest normalization** — each harness stores sessions differently.
_Avoid_: plugin, backend, driver (taken)

**harvest**:
Reading a finished session by its ID from a harness's local storage and normalizing it into a result. The shared capability behind both feeds — automated runs additionally *invoke* the harness, manual runs do not.
_Avoid_: collect, ingest, import, scrape

**session**:
A harness's *own* unit of work, addressed by its session ID. Koalaty harvests a session into a **result**; "session" stays harness-side and is never used for koalaty's own records.
_Avoid_: (don't use this word for koalaty's run or result)

## Core nouns

**task**:
The version-controlled bundle koalaty owns and holds fixed across models: the prompt text, the done-condition, the starting fixture (*gum*), and eval assets. One per directory.
_Avoid_: prompt (that's only the text), fixture, case, scenario

**prompt**:
The text pasted into the harness to start a session. A field inside a **task**, not a thing on its own.
_Avoid_: instruction, query

**example task**:
A real, ordinary task bundled with koalaty for onboarding, copied into the user's `tasks/` as a starting point. Running one produces a real result — an example task is *not* a **joey**.
_Avoid_: sample, demo, template

**task config**:
A **task**'s own authored settings (`task.toml`): its `turns`, `tags`, `gum`, and friends. Part of the task bundle. Distinct from koalaty's own **configuration** (the packaged `koalaty.toml` registry of settings + invariants, see [ADR-0006](docs/adr/0006-configuration-via-configaroo.md)) — reserve bare "config"/"configuration" for the latter.
_Avoid_: config (use that for koalaty's own settings)

**drop-bear**:
A **task** tag marking an adversarial / red-team task — about *what was asked*. Lets comparisons filter to adversarial tasks.
_Avoid_: adversarial (use the tag), red-team

**joey**:
A **run** flag marking a throwaway trial run that should not count — about *whether this run counts*. Recorded on the result; excluded from `compare` by default.
_Avoid_: trial, smoke, draft

**run**:
One evaluation of one task by one model in one harness — automated or manual. The activity, not the record. A manual run is **pending** between `start` (prompt issued) and `harvest` (session collected); a pending run lives in the pouch awaiting its session.
_Avoid_: trial, attempt, execution, eval

**result**:
The normalized, stored record a run produces and that lives in the **pouch**. The comparable artifact.
_Avoid_: report, record, output, outcome

**driver**:
Who steers the session: `koalaty` (automated run — koalaty invokes the harness, then harvests) or `human` (manual run — you drive in your own terminal, koalaty harvests by session ID). *Derived from the feed that produced the run*, not authored: the manual feed (`start`/`harvest`) always records `human`; the automated feed (`run`) always records `koalaty`. Which feed a task may use is a separate **routing** rule (an `interactive` task or a harness with no headless mode is manual-only); a human may still choose the manual feed for an otherwise-automatable task, and `driver` then honestly records `human`. Recorded on the **result** for filtering.
_Avoid_: mode, runner, source

**gum**:
The starting fixture a task runs against — the repo state / environment ("which tree are we running in"): inline files, or a git URL + pinned commit. Part of the **task**.
_Avoid_: fixture, setup, env, sandbox

**run id**:
The self-describing label naming a **run**'s directory in the **pouch**: `<task>-<harness>-<model>-<date>-<shortid>` (e.g. `quokka-fake-opus48-20260618-a1b2c3`). A human-readable label only — `result.json` is authoritative; code never parses the id for information (see [ADR-0003](docs/adr/0003-run-id-ordering-and-canonical-names.md)).
_Avoid_: run name, slug, key

**canonical name**:
The short, dash-free slug koalaty uses for a **harness** (`claudecode`, `copilot`, `codex`, `opencode`, `fake`) or a model (`opus48`, `sonnet46`, `glm51`, `gpt55`, `gpt53codex`, …). Keeps each **run id** field unambiguous. Harness names are bounded by which **adapters** exist; model names match `^[a-z0-9]+$` with no central registry.
_Avoid_: short name, alias, slug (use this term)

## Evaluation

**paws**:
The later, re-runnable grading pass computed over results in the pouch. Produces scores from two tracks: **mechanical** and **rubric**. Distinct from **survey**, which is captured earlier at harvest.
_Avoid_: grade, score (the verb), eval, judge

**mechanical**:
The objective track of paws: facts derived from a result's artifacts — patch applies, build passes, tests pass, lint clean. Pass/fail or numeric. Applies to all runs.
_Avoid_: automatic, objective

**rubric**:
The subjective track of paws: quality of the output/transcript against shared criteria, scored third-person by an LLM-judge and/or a human reviewer. Applies to all runs. (The reviewer may be the driver; if so, blinding is lost — handle later.)
_Avoid_: criteria, judge (use for the scorer, not the track)

**survey**:
First-person feedback from the human **driver** on how the session felt — friction, hand-holding, frustration, plus free-text notes. Captured at harvest, manual runs only, stored on the **result**. Not part of paws.
_Avoid_: feedback, questionnaire, review (that's rubric)

**turns**:
A **task** property describing turn structure: `one-shot`, `scripted` (a fixed, ordered list of follow-up turns), or `interactive` (next turn needs human judgment). `one-shot`/`scripted` run under either driver; `interactive` is manual-only. Tool-permission prompts are pre-authorized run config, not turns.
_Avoid_: mode, multi-turn, conversation
