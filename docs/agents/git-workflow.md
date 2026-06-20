# Git workflow

How an agent uses git when implementing an issue. The maintainer reviews PRs and **squash-merges** them, so the goal is a clean, reviewable, one-PR-per-issue history.

## Implementing an assigned issue

The end-to-end loop for a session that picks up an issue:

1. **Read the issue.** `gh issue view <n>` — the body's tasks and acceptance criteria are your worklist.
2. **Branch off `main` in a new worktree.** Never commit to `main`. Name the branch `agent/<issue#>-<slug>`, e.g. `agent/12-walking-skeleton`, and create it in its own worktree so several implementations can proceed in parallel: `git worktree add ../koalaty-<issue#>-<slug> -b agent/<issue#>-<slug> main`. Do the rest of the work from that worktree directory. Each worktree gets its own gitignored `/pouch/`, so parallel runs keep their data isolated and never collide.
3. **Work test-first.** Use the `tdd` skill (red → green → refactor); see [testing.md](./testing.md) for what to test and the seam/boundary rules.
4. **Tick the checklist as you go.** As each acceptance-criterion / task checkbox is satisfied *and verified* (tests + `just check` green), check it off in the issue — see [Tracking progress](#tracking-progress) below.
5. **Commit regularly** — small checkpoint commits at each green step keep progress legible and recoverable. Because the PR is squash-merged, individual commit messages are throwaway; keep them short and imperative.
6. **Gate before publishing.** `just check` must pass (see [quality-gates.md](./quality-gates.md)) before you push or open the PR.
7. **Push** the branch and **open a PR** (ready, not draft) once the gate is green.
8. The maintainer reviews and **squash-merges**.

## Tracking progress

Keep the issue's checkboxes current so the maintainer can see progress at a glance:

- A box is checked **only when its item is done and verified** (the relevant test passes and `just check` is green) — never check ahead of working code.
- Flip `- [ ]` → `- [x]` by editing the issue body: `gh issue view <n> --json body --jq .body > /tmp/issue.md`, edit, `gh issue edit <n> --body-file /tmp/issue.md`.
- Batch the updates at meaningful milestones rather than one edit per box, to avoid churn.
- If you discover a checklist item is wrong or missing, fix the list (and say so in the PR) rather than silently skipping it.

## Commits

- End every commit message with the trailer:
  ```
  Co-Authored-By: Your model name <your email>
  ```
- Never commit the **pouch** or other run data — it is gitignored (`/pouch/`); results never belong in a PR.

## The PR

- **One PR per issue.**
- The **PR title is what lands in history** (squash merge), so make it a clean [Conventional Commit](https://www.conventionalcommits.org/): `feat: …`, `fix: …`, `chore: …`, `docs: …`, `test: …`, `refactor: …`.
  - e.g. `feat: walking skeleton run → pouch → compare`
- Write the body with the `pr-description` skill. Include `Closes #<issue>` so the merge auto-closes the issue.
- Open the PR **ready for review** (not draft) once `just check` is green.

## Authorization

This file is standing authorization for implementing agents to branch, commit, push, and open PRs for an assigned issue without asking each time. It does **not** authorize merging — the maintainer merges.
