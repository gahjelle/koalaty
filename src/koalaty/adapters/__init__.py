"""Adapters package: the adapter protocol and its harness registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from koalaty.adapters.fake import FakeAdapter

if TYPE_CHECKING:
    from koalaty.adapters.base import Adapter

# The harness registry: a harness is known only if an adapter exists for it.
_REGISTRY: dict[str, type[Adapter]] = {FakeAdapter.name: FakeAdapter}


def known_harnesses() -> list[str]:
    """Return the canonical names of every registered harness."""
    return sorted(_REGISTRY)


def get_adapter(harness: str) -> Adapter | None:
    """Return a fresh adapter for ``harness``, or ``None`` if unregistered."""
    adapter_cls = _REGISTRY.get(harness)
    return adapter_cls() if adapter_cls is not None else None
