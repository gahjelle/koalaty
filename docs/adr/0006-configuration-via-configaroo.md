# Configuration via configaroo: a packaged registry and global singleton

Koalaty's literal values — both user-facing settings (pouch/tasks locations) and
fixed invariants (task filenames, the task-id pattern, the model/canonical-name
pattern, turn separator, result/run-id layout) — are collected into one packaged
TOML registry, `src/koalaty/config/koalaty.toml`, loaded once via
[configaroo](https://github.com/gahjelle/configaroo) into a frozen `Config`
pydantic model exposed as a module-global singleton (`from koalaty.config import
config`). This grew out of issue #22, where `scaffold.py` reached into
`tasks.py` for non-`__all__` constants: rather than re-home a few constants, we
gave every value a single home so cross-module literals are read from `config`
(`config.task.task_file`) instead of imported across modules.

The registry has **two layers with different override rules**. *Settings*
(`pouch`, `tasks`) are top-level keys that may be overridden, with precedence
`--pouch/--tasks flag > KOALATY_* env > packaged default`. *Invariants* live in
nested sections (`[task]`, `[model]`, `[result]`, `[run_id]`) and are **never**
env- or flag-overridable — they are contracts (e.g. scaffold-write and task-load
must agree on `task.toml`), not knobs. configaroo's `add_envs` only maps the two
settings keys explicitly (`{POUCH: pouch, TASKS: tasks}`, prefix `KOALATY_`);
nested sections are untouched by the env overlay, which is what makes the
fixed layer fixed.

The two libraries split cleanly: **configaroo owns file + env + defaults**
(resolved at import into `config.pouch`/`config.tasks`), and **cyclopts owns
CLI flags**, with `--pouch`/`--tasks` defaulting to `config.pouch`/`config.tasks`
and overriding per-invocation. The old `cyclopts.config.Env("KOALATY_")` overlay
is removed so there is exactly one env owner.

## Considered options

- **Global singleton vs dependency injection.** Settings are still DI'd as
  resolved `Path` params (`load_task(tasks_dir, ...)`), keeping per-invocation
  override and test isolation (`tmp_path`) intact. Only the import-time
  invariants are read from the global. So the singleton holds the *baseline*;
  it is not the whole story for the per-call settings.
- **Breadth of extraction.** We extract *every* literal, including
  single-module algorithm constants (`turn_separator`, `min_scripted_turns`),
  not just the cross-module set #22 forced. The maintainer prefers "configuration"
  broadly — values live in TOML, code reads them back. The cost (e.g. `tasks.py`
  now depends on the global for a private parsing detail) was accepted.
- **User/project config file: deferred.** Only the packaged TOML + env ship now.
  A user file is future work: because the registry now contains invariants, a
  user file that could override them would re-arm the #22 divergence hazard, so
  it needs settings-only merge semantics before it lands.

## Consequences

- New runtime dependency: `configaroo`. The packaged `koalaty.toml` must be
  included in the wheel; it is resolved with `Path(__file__).parent / "koalaty.toml"`.
- `config.py` becomes a `config/` package; the `Config` shape (and its
  sub-models) lives in `schemas/config.py` per ADR-0004 (shapes shared across
  modules live in `schemas/`), while loading + the singleton live in
  `config/__init__.py`.
- Run-id pieces (date format, shortid length, `result.json`, `raw/session.json`)
  move to config as *values*; the structural `<task>-<harness>-<model>-<date>-<shortid>`
  ordering stays an f-string in code (ADR-0003 — the id is a label, not parsed).
