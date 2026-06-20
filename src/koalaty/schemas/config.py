"""Configuration schemas: the shape of koalaty's packaged registry.

Two layers live here. *Settings* (`pouch`, `tasks`) are env-overridable top-level
paths; *invariants* (`task`, `model`, `result`, `run_id`) are fixed contracts
shared across modules — never overridable (see ADR-0006, ADR-0010).
"""

from pathlib import Path

from koalaty.schemas import FrozenModel, StrictModel

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
    pending_file: str


class RunId(FrozenModel):
    """Values that shape a minted run id (its structure stays in code, ADR-0003)."""

    date_format: str
    shortid_length: int


class Config(StrictModel):
    """koalaty's full configuration: settings plus fixed invariants.

    A mutable `StrictModel` (not frozen): the settings (`pouch`, `tasks`) are
    resolved once at import, but staying mutable lets tests monkeypatch them for
    isolation. The invariant sub-sections remain frozen models. See ADR-0010.
    """

    pouch: Path
    tasks: Path
    task: TaskFiles
    model: ModelRules
    result: ResultLayout
    run_id: RunId
