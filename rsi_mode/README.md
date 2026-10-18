# PRAXIST-RSI prototype tools

This directory is the executable part of the PRAXIST-RSI RFC. It is deliberately
small and conservative.

## What it does

- `promote.py` records a candidate's score, hash, correctness, metrics, and a
  human approval gate. It refuses candidates with correctness below 1.0,
  duplicate candidate hashes, and approved scores that do not exceed the best
  approved score.
- `curve.py` renders the score curve from the append-only promotion records.
- `verify.py` checks that the sealed evaluator, golden cases, baseline, and
  task contract still match their recorded hashes.

## What it does not do

- It does not modify a running PRAXIST kernel.
- It does not edit the sealed evaluator.
- It does not auto-approve a promotion. `--approve` is an explicit human action.
- It does not claim that a subsystem task is full RSI.

## Usage

```bash
python rsi_mode/promote.py \
  --candidate experiments/run_x/gen_0/variant.py \
  --generation 0 \
  --score 1.23 \
  --correctness 1.0 \
  --metrics-json '{"speedup": 1.23}' \
  --evaluator evaluations/run.py \
  --promotions promotions/promotions.jsonl

python rsi_mode/curve.py --promotions promotions/promotions.jsonl
```

## Boundary

The sealed evaluator is the judge. The candidate is a versioned artifact.
Promotion is append-only and human-gated. That is the minimum contract for a
system-level self-improvement loop that can be audited rather than trusted.
