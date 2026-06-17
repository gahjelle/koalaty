# Run-ID field order and canonical harness/model names

A run ID is `<task>-<harness>-<model>-<date>-<shortid>` (e.g. `quokka-fake-opus48-20260618-a1b2c3`). The date sits *after* the task/harness/model rather than first, and `harness`, `model`, `date`, and `shortid` are all dash-free: harnesses and models use short canonical slugs (`claudecode`, `copilot`, `codex`, `opencode`, `fake`; `opus48`, `sonnet46`, `glm51`, `gpt55`, `gpt53codex`, …) and the date is written `YYYYMMDD`.

We chose this order so a plain directory listing of the pouch groups runs by `task → harness → model`, and chronologically *within* a combo — matching the product's comparison unit, **(model × harness) per task** ([ADR-0001](./0001-pouch-is-the-product-two-feeds.md)). Date-first would optimize for "what did I run lately", which the derived **index** ([ADR-0002](./0002-files-source-of-truth-derived-index.md)) answers better anyway. Keeping every field except the task dash-free means the run ID stays unambiguously eyeball-parseable from the right even though task ids may themselves contain dashes.

## Consequences

- The run ID is a human-readable **label**; `result.json` remains the authoritative source of every field — code never parses the directory name for information.
- `--harness` and `--model` are validated to the canonical slug pattern (`^[a-z0-9]+$`); a hard registry is kept only implicitly for harnesses (an adapter must exist), never for the open-ended model set.
- The convention is part of the ubiquitous language — see `CONTEXT.md`.
