# Bundled example tasks are copy-only package data

Koalaty ships **example tasks** as package data (inside the installed wheel). `koalaty run <id>` resolves a task *only* from the configurable tasks directory (`--tasks` / `KOALATY_TASKS`, default `./tasks/`); it never runs an example in place. The single bridge from package to tasks directory is `koalaty task new [<id>] --from-example <name>`, which copies the example out, after which it is an ordinary, user-owned task.

We chose this over letting `run` fall back to bundled examples so there is exactly one resolution rule and no precedence puzzle when a user's `tasks/<id>` collides with a bundled example of the same name. It also keeps "an example becomes a real task the moment it is copied" literally true (see `CONTEXT.md`: *example task*), and means there is no special-casing of the directory you happen to run koalaty from.

## Consequences

- A new user starts from an empty `tasks/`; the onboarding path is `task new --from-example <name>` → edit → `run`, not `run <example>`.
- The headline round-trip (`run` → `compare`) for a bundled example always goes *through* a copy into the tasks directory first.
- Author convenience like resolving a branch/tag gum ref to a pinned SHA is deferred to when checkout lands; today a git gum pins a full 40-hex commit by construction.
