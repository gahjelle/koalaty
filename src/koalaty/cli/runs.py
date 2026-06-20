"""CLI commands for the run feeds: `run`, `start`, and `harvest`.

These sit alongside `koalaty.runs` (the orchestration module they delegate to);
this is the CLI face of each feed. The CLI layer stays thin: input validation
lives in the shared types, but all domain logic lives in `koalaty.runs`.

The settings paths (`config.tasks`, `config.pouch`) are read in the command
bodies, at call time, rather than bound as def-time defaults: binding once at
import would defeat the test isolation that monkeypatches `config` (ADR-0010).
The dynamic task `Literal` on `run`/`start` is applied in `build_app`.
"""

from koalaty.cli import (  # noqa: TC001 — cyclopts resolves these annotation aliases at runtime via get_type_hints
    HarnessParam,
    ModelParam,
)
from koalaty.config import config
from koalaty.console import stderr
from koalaty.runs import harvest_manual, run_automated, start_manual
from koalaty.tasks import load_task

__all__ = ["harvest", "run", "start"]


def run(
    task: str,
    *,
    harness: HarnessParam,
    model: ModelParam,
) -> str:
    """Run a task on a model in a harness and store the result in the pouch.

    Loads the task from disk, delegates to run_automated for the full
    pipeline, and returns the new run id.
    """
    loaded = load_task(config.tasks, task)
    result = run_automated(loaded, harness, model, config.pouch)
    return result.run_id


def start(
    task: str,
    *,
    harness: HarnessParam,
    model: ModelParam,
) -> str:
    """Start a manual run: write a pending run and print setup instructions.

    Loads the task, delegates to start_manual (which never invokes the harness),
    prints the harness-specific setup instructions to stderr, and returns the
    new run id on stdout.
    """
    loaded = load_task(config.tasks, task)
    pending, instructions = start_manual(loaded, harness, model, config.pouch)
    stderr.print(instructions)
    return pending.run_id


def harvest(
    run_id: str,
    *,
    session: str,
) -> str:
    """Harvest a pending manual run's externally-supplied session into a result.

    Delegates to harvest_manual, which writes result.json and removes pending.json,
    then returns the completed run id. Errors if the run id is unknown or has
    already been harvested.
    """
    result = harvest_manual(run_id, session, config.pouch)
    return result.run_id
