"""Metrics schemas: the objective resource-use a harvest normalizes off a session.

Bucketed token counts, model time (`active_ms`) versus end-to-end wallclock, and
tool-call aggregates — the comparable, harness-reported facts (see CONTEXT.md).
Dollar cost is *not* here: it is derived later against current pricing (ADR-0013).
"""

from koalaty.schemas import FrozenModel

__all__ = ["Metrics", "ModelUsage", "TokenUsage", "ToolCalls"]


class TokenUsage(FrozenModel):
    """Token counts bucketed by kind, kept separate so cost can be re-derived.

    Buckets are priced differently, so they are never collapsed into one total
    (see ADR-0013). Defaults to all-zero for a session that reported nothing.
    """

    input: int = 0
    output: int = 0
    cache_creation: int = 0
    cache_read: int = 0


class ToolCalls(FrozenModel):
    """Tool-call aggregates: how many ran, by name, and how many failed.

    Full tool I/O stays in the raw transcript; only these counts are normalized.
    """

    total: int = 0
    by_name: dict[str, int] = {}  # noqa: RUF012 — pydantic deep-copies field defaults
    failures: int = 0


class ModelUsage(FrozenModel):
    """One model the session touched, with the tokens it accounted for.

    Sessions may touch several models (a mid-session switch, sub-agents, the
    title generator); each is recorded so per-model cost can be derived (ADR-0013).
    """

    model: str
    tokens: TokenUsage


class Metrics(FrozenModel):
    """The objective resource-use normalized off a session for comparison.

    `active_ms` sums per-turn model time — the apples-to-apples model metric;
    `wallclock_ms` is end-to-end and, on manual runs, includes human idle.
    """

    tokens: TokenUsage
    active_ms: int
    wallclock_ms: int
    tool_calls: ToolCalls
