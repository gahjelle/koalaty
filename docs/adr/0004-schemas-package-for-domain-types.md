# Schemas package for domain types; exceptions module for errors

Domain types (Pydantic models, enums, discriminated unions, type aliases) live in a dedicated `schemas` package that mirrors the behavioral modules. Domain exceptions live in a single `exceptions` module with a shared base class. Behavioral modules import types from schemas; schemas never import from behavioral modules.

```
schemas/
  __init__.py       # FrozenModel (foundational base)
  tasks.py          # Turns, InlineGum, GitGum, Gum, TaskConfig, Task
  result.py         # SCHEMA_VERSION, Outcome, Result
  adapters.py       # HarvestedSession

exceptions.py       # KoalatyError, TaskLoadError
```

We chose this over scattering types alongside their behavior (the status quo) for three reasons. First, cross-module type dependencies were forcing imports behind `TYPE_CHECKING` guards — `result.py` reached into `tasks.py` for `Turns`, and `adapters/base.py` reached into both `tasks.py` and `result.py`. A schemas layer reverses the arrows: behavioral modules depend on schemas, not on each other. Second, types behind `TYPE_CHECKING` are invisible to runtime inspection and IDE navigation; moving them to a public schemas package makes them always available. Third, a single package makes the type inventory discoverable — "where is `Turns` defined?" has one answer.

The parallel naming (`schemas.tasks` / `koalaty.tasks`) is intentional: same words for the same concept, distinguished by the `schemas.` prefix. Schemas contain validation logic that enforces shape constraints (e.g. "commit must be 40 hex chars") but no behavioral methods — they are data classes in the semantic sense. Protocols stay in their behavioral modules (`adapters/base.py`) because they are behavior contracts, not shapes.

Schema version constants (`SCHEMA_VERSION`) move with their schemas. At this stage, a version mismatch is a reject gate — the reader refuses to load incompatible data. Migration readers are YAGNI until real users carry old data.

## Consequences

- Adding a new domain type means deciding: does it live in schemas (a shape shared across modules) or in the behavioral module (local to one module)? The rule of thumb: if another module needs the type, it goes in schemas.
- `models.py` and `result.py` are deleted; their contents move to `schemas/__init__.py` and `schemas/result.py` respectively.
- `TaskError` is renamed `TaskLoadError` — in a shared `exceptions` module, names must be unambiguous without their module prefix.
- All custom exceptions inherit `KoalatyError`, enabling a top-level CLI handler to catch domain errors uniformly.
