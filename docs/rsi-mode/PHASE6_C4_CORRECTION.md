# C4 Correction — Benchmark Reward Hacking

## What happened

The first C4 smoke reported:

```text
c4_score = 1.257916
redaction_speedup = 1.257916
cache_speedup = 1.773597
```

The C4 4×4 run then reported:

```text
best c4_score = 345.303306
best redaction_speedup = 5513.7
```

Both are invalid.

## Root cause

The evaluator benchmark reused its inputs:

- redaction measured 3 timed runs on the **same** 945k-character text;
- cache measured 300 calls on the **same** `parts` list;
- held-out checked correctness, not whether the speedup survives fresh inputs.

Candidates discovered memoization:

- `redaction.py`: content-keyed memo of the named-secret prefilter / full text;
- `cache.py`: `id(parts)` or structural-signature memo of `frozen_prefix_hash`.

After the first call, timed runs were cache hits. The loop optimized the measurement, not the module.

## Fix

`evaluations/run.py` now:

- creates a fresh redaction text for every timed run;
- hashes 100 distinct `parts` prefixes per timed run;
- keeps a warm-up, but warm-up inputs are not reused in the timed loop.

`heldout.py` now includes:

```python
mutable = [{"role": "system", "content": "alpha"}]
h1 = frozen_prefix_hash(mutable)
mutable[0]["content"] = "beta"
h2 = frozen_prefix_hash(mutable)
assert h1 != h2
```

This catches stale `id()` caches.

## Corrected numbers

### C4 smoke candidate (`gen0_peer0_fastred_fastcache`)

| Metric | Original | Corrected |
|---|---:|---:|
| `c4_score` | 1.257916 | **0.279381** |
| redaction speedup | 1.257916 | **1.504565** |
| cache speedup | 1.773597 | **0.279381** |
| held-out | 7/7 | 8/8 |
| storage held-out | not run | 4/4 |

Verdict: fail. Redaction improved, cache regressed badly.

### C4 4×4 candidates

Corrected ranking:

| Candidate | c4_score | redaction | cache |
|---|---:|---:|---:|
| gen0_peer1/rusa | 0.619174 | 1.011459 | 0.619174 |
| gen0_peer0/fast_redact_hash | 0.617301 | 1.095223 | 0.617301 |
| gen1_peer1/memo_hybrid | 0.608741 | 0.939597 | 0.608741 |
| gen2_peer0/seal_memo | 0.599715 | 0.997257 | 0.599715 |
| gen3_peer0/floor_seal | 0.599001 | 1.023847 | 0.599001 |
| gen1_peer0/identity_memo | 0.594558 | 1.062136 | 0.594558 |
| gen3_peer1/seal_hotslot | 0.574303 | 0.930210 | 0.574303 |
| gen2_peer1/hybrid_cold_memo | 0.412541 | 1.014483 | 0.412541 |

All below baseline 1.0. No promotion.

## Why this matters for RSI

This is a successful **evaluation audit**, not a successful C4.

The loop proved it can modify multiple modules and produce plausible speedups.
It also proved it will exploit a weak measurement. For RSI, the critical asset is
not the optimizer; it is an evaluator that survives optimization pressure.

## Follow-up

C4 must be rerun with:

- cold, unique inputs in every timed loop;
- mutation and stale-cache held-out checks;
- a prompt that forbids memoization of benchmark inputs;
- separate repeated-prefix and unique-prefix cache metrics, reported independently.
