"""Reference top-k implementation.

This file is outside the candidate workspace and must not be edited by peers.
"""

from __future__ import annotations

from typing import Iterable, List


def top_k(items: Iterable[int], k: int) -> List[int]:
    """Return the k largest items in descending order."""
    values = list(items)
    if k <= 0:
        return []
    return sorted(values, reverse=True)[:k]
