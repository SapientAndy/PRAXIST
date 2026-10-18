# Bug set v1 — self-repair starting state

Four deterministic regressions are injected into `workspace/praxist`. They are
small, local, and each is caught by the sealed tests. The research loop may edit
`workspace/praxist/**` to repair them; it may not edit `sealed_tests/` or
`evaluations/run.py`.

| # | File | Injected change | Sealed test that catches it |
|---|---|---|---|
| 1 | `praxist/core/runtimes.py` | default reasoning effort `max` → `high` (three fallback sites) | `test_reasoning_policy_parses_and_preserves_premium_compatibility` |
| 2 | `.../backend/artifact_semantics.py` | `is_runtime_fact_source`: `is True` → `is False` | `test_semantics_distinguish_canonical_state_from_derived_views` |
| 3 | `.../backend/artifact_semantics.py` | `explicit_entry_generation_id`: `max(...)` → `min(...)` | `test_explicit_entry_generation_uses_latest_recorded_provenance_only` |
| 4 | `.../backend/agent.py` | lossless limits `48/24_000` → `32/16_000` | `test_lossless_continuation_keeps_full_task_and_uses_larger_finding_batch` |

## Measurements

| State | Passed / total | Pass rate |
|---|---|---|
| Clean baseline | 54 / 55 | 0.9818 |
| Degraded v1 | 50 / 55 | 0.9091 |

The fifth failure in the degraded run is the known `agent_runtime:fake_runtime`
plugin-discovery issue, present in both states. It is not part of the bug set.

## Success criterion

Restore **54 / 55** (the clean baseline) without touching the sealed tests or
the evaluator. A run that only reaches 53/55 has fixed three of four bugs and
must not be promoted.

## Why these bugs

They are not arbitrary syntax errors. Each one changes a semantic contract that
the project's own tests defend: reasoning defaults, artifact fact ownership,
generation provenance, and context-efficiency limits. A repair requires reading
the code and the test contract, not pattern-matching an error message.
