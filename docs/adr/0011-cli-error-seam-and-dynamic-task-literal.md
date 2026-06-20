# CLI error seam: a meta-launcher box plus an early task `Literal`

Two parse-stage-style boxes, one consistent look. cyclopts already renders a red
"Error" panel for **parse-stage** errors (an unknown command, a bad option). Two
classes of error did *not* get that treatment and dumped a raw traceback
instead; this ADR records how each is now caught early and boxed.

## A meta-launcher catches domain errors

A `koalaty run quokka --harness fake --model sonnet` whose task fails to load
raises `TaskLoadError` **inside the command body**, after parsing — so cyclopts'
`error_formatter` (which only fires for `CycloptsError`) never sees it. We catch
it one level out, at an execution seam: `build_app()` registers an
`app.meta.default` launcher that wraps `app(tokens)`:

```python
@app.meta.default
def launcher(*tokens):
    try:
        app(tokens)
    except KoalaError as error:
        print_error(error)        # Rich box, mimics cyclopts' panel
        raise SystemExit(1) from error
```

`__main__.main()` calls `build_app().meta()` instead of `build_app()()`.

- **Catch `KoalaError` only.** Every domain error subclasses it, so domain
  failures get a friendly box and a non-zero exit. Genuine bugs (`KeyError`,
  `AttributeError`, …) are *not* caught and still raise a full traceback, so they
  stay debuggable.
- **One renderer.** A new `console.print_error` renders a red `Error` panel that
  mimics cyclopts' parse-error box, keeping Rich output centralized per
  [ADR-0007](0007-console-module-stdout-stderr.md). A test asserts the domain
  box and the cyclopts parse box share their framing.
- Parse errors are unaffected — they still exit through cyclopts' own box.

### Why the meta indirection rather than a `try/except` in `main()`?

- **A `try/except` in `__main__.main()`** would work for the real entry point,
  but tests drive the app through the `app(...)` object, not `main()`; the seam
  belongs on the app so both paths share it. The meta-app is cyclopts' supported
  place to wrap invocation.
- **Translating domain errors into `CycloptsError`** so `error_formatter` could
  render them was rejected: it would couple domain modules to cyclopts' exception
  hierarchy and blur the parse-vs-execute boundary the box look is meant to keep.

## An early task `Literal` rejects unknown tasks up front

`run` / `start` annotate their `task` parameter with a `Literal` of the task ids
found in `config.tasks` at `build_app()` time (an empty/missing tasks dir falls
back to plain `str`). An unknown task is then a **parse-stage** rejection with
cyclopts' own box — before `--harness`/`--model` are even required. This relies
on settings being import-time knowable, which is why the flags had to go
([ADR-0010](0010-settings-env-only-mutable-config.md)).

- **`Literal`, not `Enum`.** cyclopts matches `Enum` by member *name* (valid
  Python identifiers only); task ids allow dashes and digit-leading values
  (`3d-render`), which `Enum` names cannot represent. `Literal[tuple(ids)]` takes
  arbitrary strings, and the cyclopts docs recommend `Literal` for choices.
- **Built by cloning the handler.** cyclopts derives choices from the parameter
  annotation, so `build_app()` clones `run`/`start` and swaps the `task`
  annotation for the `Literal` (the real type object, so cyclopts resolves it
  without the build-time closure in scope). The module-level functions are left
  untouched. `list_task_ids(tasks_dir)` (in `tasks.py`, parallel to
  `known_harnesses()`) supplies the ids.
- `compare`'s `task` (a filter over pouch results) and `task_new`'s `task` (a
  *new* id that must not yet exist) stay plain `str`.

### Observed ordering

`koalaty run asdf` (no `--harness`) reports the bad task first —
`Invalid value "asdf" for TASK. Choose from: "quokka".` — rather than the
missing required option. So an unknown task surfaces immediately, which was the
goal. With an empty tasks dir, `task` falls back to `str`, `asdf` passes parsing,
and the unknown task is caught at load time and boxed by the meta launcher
instead.

## Consequences

- `console.print_error` is the single domain-error renderer; `__main__` runs the
  app via `.meta()`.
- The dynamic `Literal` is rebuilt on every `build_app()`, so it always reflects
  the current `config.tasks` (which tests monkeypatch before building the app).
