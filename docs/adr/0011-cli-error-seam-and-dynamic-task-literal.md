# CLI error seam: a meta-launcher box plus an early task validator

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

## A `TaskParam` validator rejects unknown tasks at parse time

`run` / `start` annotate their `task` parameter with `TaskParam` — a `str`
annotated with a cyclopts `Parameter(validator=validate_task)`. The validator
checks `config.tasks` at parse time and raises `ValueError` for an unknown task
id, so cyclopts renders its own error box — before `--harness`/`--model` are
even required. This relies on settings being import-time knowable, which is why
the flags had to go ([ADR-0010](0010-settings-env-only-mutable-config.md)).

- **Validator, not `Literal`.** An earlier version used a dynamic `Literal` of
  task ids injected by cloning each handler function and swapping the `task`
  annotation at `build_app()` time. That gave choices in `--help` but required
  `types.FunctionType` cloning and a `# ty: ignore` for the runtime `Literal`
  tuple. A validator is strictly simpler — same early rejection, same error
  wording (cyclopts prepends `"Invalid value" for TASK` to the `ValueError`),
  and no metaprogramming. The trade-off is that available tasks don't appear as
  `[choices: ...]` in `--help`; only in the error message on a bad value.
- **Validator, not `Enum`.** cyclopts matches `Enum` by member *name* (valid
  Python identifiers only); task ids allow dashes and digit-leading values
  (`3d-render`), which `Enum` names cannot represent. A validator accepts
  arbitrary strings.
- `list_task_ids(tasks_dir)` (in `tasks.py`, parallel to `known_harnesses()`)
  supplies the ids.
- `compare`'s `task` (a filter over pouch results) and `task_new`'s `task` (a
  *new* id that must not yet exist) stay plain `str`.

### Observed ordering

`koalaty run asdf` (no `--harness`) reports the bad task first —
`Invalid value "asdf" for TASK. Choose from: quokka.` — rather than the
missing required option. So an unknown task surfaces immediately, which was the
goal. With an empty tasks dir, the validator still fires and rejects the value
(cyclopts' own box), rather than deferring to a load-time `TaskLoadError`.

## Consequences

- `console.print_error` is the single domain-error renderer; `__main__` runs the
  app via `.meta()`.
- `TaskParam` in `cli/__init__.py` is the single early-task-validation point;
  `run`/`start` use it directly, no build-time annotation swapping needed.
