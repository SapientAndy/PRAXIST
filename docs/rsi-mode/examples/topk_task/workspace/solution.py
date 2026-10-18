"""Candidate top-k implementation.

Only this file may be edited by peers. Preserve the exact contract:

- return the k largest items in descending order;
- return [] when k <= 0;
- preserve duplicates.
"""

from __future__ import annotations

from typing import Iterable, List


def top_k(items: Iterable[int], k: int) -> List[int]:
    values = list(items)
    if k <= 0:
        return []
    return sorted(values, reverse=True)[:k]
