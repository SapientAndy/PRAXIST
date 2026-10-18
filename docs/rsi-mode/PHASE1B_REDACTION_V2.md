# Phase 1b — Redaction v2: safe parent continuation

**Status: subsystem-level self-improvement. Not full PRAXIST RSI.**

## Question

After the first redaction run found fast-but-unsafe candidates, can the loop
continue improving a **safe** parent without breaking the hardened 29-case
contract?

## Setup

- Start workspace: `span_slice`, the only candidate that passed the 29-case
  sealed evaluator and the 1,200-case differential fuzz.
- Sealed evaluator: 29 cases, including cross-line bearer/named/password,
  duplicate secrets, and Unicode length change.
- Baseline: `span_slice`, `baseline_median_ms = 14.8998`, score `1.0`.
- Candidate surface: `workspace/redaction.py` only.
- Generations: 2; cohort: 2; DeepSeek API; `agent_runtime:claude_sdk`.

## Results

| Generation | Candidate | Correctness | Median ms | Relative score | External fuzz |
|---|---|---|---:|---:|---|
| baseline | `span_slice` | 29/29 | 14.8998 | 1.0000 | 0/1,200 |
| gen 0 | `gen0_peer0_prefilter` | 29/29 | 14.3552 | 1.0379 | not separately audited |
| gen 1 | `gen1_peer1_gated` | 29/29 | **4.4892** | **3.3190** | **0/1,200** |

The gen-1 candidate is about **22.5x faster than the pristine module**
(100.9227 ms → 4.4892 ms) while preserving all 29 sealed cases and the
1,200-case differential fuzz. That absolute number is a conversion against the
pristine benchmark; the sealed evaluator's primary score is the relative
3.3190 against the safe parent.

## What this shows

- The loop can improve a **safe** parent, not only find a fast candidate from
  the pristine version.
- The hardened evaluator and the differential fuzz agree on the gen-1 candidate.
- The human promotion gate still holds: the record is `proposed`, not approved.

## What this does not show

- It is one module, not the PRAXIST kernel.
- The benchmark is synthetic and in-distribution; no held-out set yet.
- The objective, metric, baseline, and promotion remain human inputs.
- It is not model-level RSI; weights are unchanged.

## Artifacts

- `gen0_eval.json`, `gen0_candidate.py`
- `gen1_eval.json`, `gen1_candidate.py`
- `promotions.jsonl`, `curve.svg`
- `gen0_boundary.json`, `gen1_boundary.json`
- `run_summary.json`
- `protected_manifest.json`, `baseline.json`
- `diff_fuzz.py`

## Reproduce

```bash
cd /home/andyl/PraxistExamples/praxist_redaction_speed_v2
python3 evaluations/run.py --workspace experiments/run_v2_direct_1/variants/gen1_peer1_gated
python3 /home/andyl/diff_fuzz.py
```
