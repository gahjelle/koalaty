# Settings are env-only; `Config` is a mutable `StrictModel`

The two settings (`pouch`, `tasks`) are no longer CLI flags. They are resolved
once at import — `KOALATY_POUCH` / `KOALATY_TASKS` env var, else the packaged
default — and read from the `config` singleton (`config.pouch`, `config.tasks`)
in the command bodies. The `--pouch` / `--tasks` flags are dropped. This
**supersedes the flag half of [ADR-0006](0006-configuration-via-configaroo.md)**:
configaroo still owns file + env + defaults, but cyclopts no longer owns a
per-invocation override for these two keys. The invariant layer is unchanged.

This is what unblocks early task-name validation
([ADR-0011](0011-cli-error-seam-and-dynamic-task-literal.md) covers the error
seam; the dynamic task `Literal` is the other half). The valid task ids live
under the tasks dir. While the tasks dir was a per-invocation `--tasks` flag,
parsed in the same pass as `run`'s `task` argument, a build-time choice list
could not honor it and a cyclopts validator could not cleanly see a sibling
argument. The env var and packaged default, by contrast, are known at **import**
— before `build_app()` — so once they are the *only* sources, `build_app()` can
read `config.tasks` and build a `Literal` of the ids up front.

`Config` becomes a **mutable `StrictModel`** — `extra="forbid"` but not
`frozen` — instead of a `FrozenModel`. `schemas/__init__.py` now has
`StrictModel` (strict, mutable) as the base, and `FrozenModel` subclasses it to
add freezing; the invariant sub-sections (`task`, `model`, `result`, `run_id`)
stay `FrozenModel`. Only the top-level `Config` is mutable, and only its two
settings change in practice.

## Considered options

- **Why drop the flags rather than keep both flag and env?** Keeping `--tasks`
  re-arms the exact problem: the choice list would have to honor a flag parsed in
  the same pass, which cyclopts cannot do cleanly. One override owner (env) keeps
  the task `Literal` correct and the precedence story simple.
- **Test isolation: monkeypatch `config` vs. dependency injection.** The old
  suite isolated to `tmp_path` by threading `--tasks`/`--pouch` through the
  `app([...])` fixture (the DI path ADR-0006 preserved). With the flags gone,
  isolation moves to **monkeypatching the now-mutable `config`** in an autouse
  conftest fixture (`monkeypatch.setattr(config, "tasks", tmp_path / "tasks")`,
  same for `pouch`). Mutability exists *for* this: a frozen `Config` could not be
  patched, and binding settings as def-time defaults
  (`def run(..., tasks_dir=config.tasks)`) would freeze the value at import and
  defeat the patch — so commands read `config.tasks` in the body at call time.
- **User/project config file: still deferred** (as in ADR-0006). Env + packaged
  default only.

## Consequences

- `cli/runs.py`, `cli/compare.py`, `cli/task.py` drop their `pouch_dir` /
  `tasks_dir` parameters and read `config.pouch` / `config.tasks` in the body.
  The shared `PouchOption` / `TasksOption` parameter types are removed.
- `KOALATY_POUCH` / `KOALATY_TASKS` are now the *primary* override path; the
  existing env+subprocess test (`test_pouch_env_var_overrides_default`) stays
  valid and gains importance.
- The CLI end-to-end suite isolates by monkeypatching `config`; the `app`
  fixture builds *after* the autouse `isolate_config` fixture so the dynamic
  task `Literal` reflects the patched `config.tasks`.
