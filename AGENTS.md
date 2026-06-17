# Agent skills

### Issue tracker

Issues live in GitHub Issues (uses the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Engineering

When implementing an issue: branch off `main` (`agent/<issue#>-<slug>`), work **test-first using the `tdd` skill**, **tick the issue's checklist** as each item is done and verified, keep `just check` green, and open a PR that the maintainer squash-merges. Full procedure in `docs/agents/git-workflow.md`.

- **Git workflow & issue procedure** — `docs/agents/git-workflow.md`.
