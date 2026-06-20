"""Configuration schemas: the shape of koalaty's packaged registry.

Two layers live here. *Settings* (`pouch`, `tasks`) are overridable top-level
paths; *invariants* (`task`, `model`, `result`, `run_id`) are fixed contracts
shared across modules — never env- or flag-overridable (see ADR-0006).
"""

from pathlib import Path

from koalaty.schemas import FrozenModel

__all__ = ["Config", "ModelRules", "ResultLayout", "RunId", "TaskFiles"]


class TaskFiles(FrozenModel):
    """Task-bundle invariants that scaffold-write and task-load must agree on."""

    task_file: str
    prompt_file: str
    done_file: str
    rubric_file: str
    id_pattern: str
    turn_separator: str
    min_scripted_turns: int


class ModelRules(FrozenModel):
    """Rules for a model's canonical name."""

    name_pattern: str


class ResultLayout(FrozenModel):
    """Filenames a run writes into its pouch directory."""

    result_file: str
    raw_session_file: str


class RunId(FrozenModel):
    """Values that shape a minted run id (its structure stays in code, ADR-0003)."""

    date_format: str
    shortid_length: int


class Config(FrozenModel):
    """koalaty's full configuration: overridable settings plus fixed invariants."""

    pouch: Path
    tasks: Path
    task: TaskFiles
    model: ModelRules
    result: ResultLayout
    run_id: RunId
