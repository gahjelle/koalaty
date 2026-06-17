# Git workflow

How an agent uses git when implementing an issue. The maintainer reviews PRs and **squash-merges** them, so the goal is a clean, reviewable, one-PR-per-issue history.

## The loop

1. **Branch off `main`.** Never commit to `main`. Name the branch `agent/<issue#>-<slug>`, e.g. `agent/12-walking-skeleton`.
2. **Commit regularly** as you work — small checkpoint commits at each green step keep progress legible and recoverable. Because the PR is squash-merged, individual commit messages are throwaway; keep them short and imperative.
3. **Gate before publishing.** `just check` must pass (see [quality-gates.md](./quality-gates.md)) before you push or open the PR.
4. **Push** the branch and **open a PR** (ready, not draft) once the gate is green.
5. The maintainer reviews and **squash-merges**.

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
