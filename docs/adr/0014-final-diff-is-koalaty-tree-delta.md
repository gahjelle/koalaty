# The final diff is koalaty's tree-delta vs gum, not adapter-normalized

The adapter normalizes only session-internal facts from the transcript (messages, tokens, timings, tool-call aggregates, session status). The **final diff** is koalaty's job, not the adapter's: koalaty owns the gum baseline, so it computes the diff as `git diff(gum baseline .. post-session worktree)`.

## Why

A harness transcript has no ready-made final patch, and reconstructing one by folding the tool-edit stream misses changes made through `bash` (a `sed`, a formatter, a `mv`) — undercounting what the model actually did. A git tree-delta against the pinned gum captures the true net effect and is harness-agnostic (every harness edits files; koalaty diffs the tree regardless). It also keeps harvest-normalization tests pure-transcript: a JSONL fixture is sufficient, with no working tree to snapshot.

## Consequences

- For a manual run, `start` resolves the gum to a baseline commit and records it plus the worktree on the pending run; `harvest` diffs that worktree against the baseline (the baseline is pinned before the human starts working, the honest moment).
- Diff capture is a separate concern from transcript normalization, with its own tests, and touches `start`/`PendingRun`.
