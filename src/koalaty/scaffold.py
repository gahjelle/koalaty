"""Writing a blank task scaffold to disk: the `task new` write path.

Complements `tasks.py` (the read path). `scaffold_task` writes the full
documented task layout with valid placeholder content, so an author starts
from a skeleton that loads and runs through `run` unedited (see ADR-0004).
"""

import re
from pathlib import Path

from koalaty.config import config
from koalaty.exceptions import TaskScaffoldError

__all__ = ["scaffold_task"]

TASK_ID_RE = re.compile(config.task.id_pattern)

TASK_TOML = """\
# turns: turn structure — "one-shot" (one prompt), "scripted" (turns separated
# by bare `---` lines in prompt.md), or "interactive" (manual-only).
turns = "one-shot"

# tags: task tags, e.g. "drop-bear" to mark an adversarial / red-team task.
tags = []

# title/description: optional human-friendly text; title defaults from the id.
# title = "..."
# description = "..."

# [gum]: the starting fixture. "inline" keeps files under this task's gum/.
# For a pinned git checkout instead, replace the block below with:
#   [gum]
#   type = "git"
#   url = "https://example.com/repo.git"
#   commit = "<full 40-char hex SHA>"
[gum]
type = "inline"
"""

PROMPT_MD = "TODO: write the prompt the harness starts the session with.\n"
DONE_MD = "TODO: describe when this task is done.\n"
RUBRIC_MD = "TODO: list the rubric criteria for grading this task.\n"


def scaffold_task(tasks_dir: Path, task_id: str) -> Path:
    """Write a blank task scaffold under `tasks_dir/<task_id>/` and return it.

    Rejects an id that breaks the task-id pattern, and refuses to overwrite an
    existing directory — writing nothing in either case.
    """
    if not TASK_ID_RE.fullmatch(task_id):
        msg = f"invalid task id {task_id!r}; must match {TASK_ID_RE.pattern}"
        raise TaskScaffoldError(msg)

    task_dir = tasks_dir / task_id
    if task_dir.exists():
        msg = f"task {task_id!r} already exists at {task_dir}; refusing to overwrite"
        raise TaskScaffoldError(msg)

    (task_dir / "gum").mkdir(parents=True)
    (task_dir / "tests").mkdir()
    (task_dir / config.task.config_file).write_text(TASK_TOML, encoding="utf-8")
    (task_dir / config.task.prompt_file).write_text(PROMPT_MD, encoding="utf-8")
    (task_dir / config.task.done_file).write_text(DONE_MD, encoding="utf-8")
    (task_dir / config.task.rubric_file).write_text(RUBRIC_MD, encoding="utf-8")
    return task_dir
