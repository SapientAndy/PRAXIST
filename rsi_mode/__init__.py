"""PRAXIST-RSI prototype utilities.

These utilities do not turn PRAXIST into an autonomous, self-modifying system.
They make the promotion boundary explicit: a sealed evaluator produces a score,
a candidate is hashed, and a human gate approves or rejects the record.
"""

from .promote import main as promote_main  # noqa: F401

__all__ = ["promote_main"]
