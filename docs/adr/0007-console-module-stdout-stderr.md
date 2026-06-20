# Console module: two shared Rich consoles split by stream

Koalaty's terminal output goes through two module-global Rich `Console`
singletons in `koalaty/console.py` — `stdout` (`Console()`) and `stderr`
(`Console(stderr=True)`) — imported by name (`from koalaty.console import
stdout, stderr`) instead of each command instantiating its own `Console()`
ad hoc. The split encodes a Unix convention: **stdout carries the primary
"product" output** a user might pipe or capture (the `compare` grid, the
`task examples` list), while **stderr carries diagnostics** (status, warnings,
"no runs found", and future errors). This lets `koalaty compare > grid.txt`
capture only the grid without the chatter.

## Considered options

- **Singletons vs. factory functions.** Plain import-time singletons, no
  factory. A fileless Rich `Console` resolves `sys.stdout`/`sys.stderr`
  lazily on each write, so the singletons still respect pytest's `capsys`
  swap — testability is not a reason to prefer factories, and factories would
  add ceremony at every call site.
- **Object naming.** `stdout`/`stderr` over `out`/`err`: the mild
  stream/console conflation (`stdout` is a `Console`, not a stream) is worth
  less than being explicit about destination at every import and call site.
- **Theme/config deferred.** Both consoles are bare `Console(...)`. A shared
  `Theme` (semantic colors replacing the inline `[green]`/`[dim]` markup in
  `compare.py`) is a real feature with its own design; folding it into this
  plumbing refactor would scope-creep it. The module is the seam where it can
  later land in one place.

## Consequences

- The new module is imported only by the CLI layer (`cli/main.py`).
  `compare.py` stays pure: `build_grid`/`render_grid` return a `Table` and the
  CLI prints it; the rendering module does not import the consoles.
- `show_config` is unchanged — it delegates to configaroo's
  `print_configuration`, which owns its own internal Rich console and cannot
  be routed through ours without reaching into configaroo.
- `compare`'s "no runs found" message moves from stdout to stderr, so its test
  (`test_compare_friendly_when_empty`) asserts on `capsys.readouterr().err`.
