# RSI Task Boundary (v0.1)

This is the minimum boundary a task must satisfy before we call it an RSI task.
It is enforced by `rsi_mode/boundary.py`.

## Required layout

```text
task-project/
  task.yaml
  workspace/                 candidate-owned, writable
  evaluations/run.py         evaluator-owned, read-only to candidate
  sealed_tests/              held-out checks, read-only to candidate
  assets/baseline.json       measured baseline
  promotions/promotions.jsonl append-only decision log
```

## Required properties

- Evaluator and sealed tests are **outside** `workspace/`.
- Candidate cannot edit `evaluations/`, `sealed_tests/`, `assets/`, or `task.yaml`.
- Baseline is measured, not guessed.
- Promotion log is append-only and records `proposed` / `approved`.
- The candidate is a copy of the system being improved, not the live engine.
- Human approval is required for promotion.

## Check

```bash
python rsi_mode/boundary.py --task-project <task-project> --json-out boundary.json
```

`rsi_ready=true` means the boundary is structurally valid. It does **not** mean the task is a good RSI benchmark.

## Current status

`praxist_kernel_speed_v6` passes the boundary:

- workspace: `workspace/praxist/`
- evaluator: `evaluations/run.py`
- sealed tests: `sealed_tests/`
- baseline: `assets/baseline.json`
- promotions: `promotions/promotions.jsonl`
- approved record: `approval_55f5baf017f9`

But it is still **subsystem-level**: the approved candidate changes redaction,
not the research loop's multi-module behavior. A full kernel RSI task must show
improvement on a cross-module, cross-task benchmark before we use the phrase
"PRAXIST RSI".

## What is still missing

1. A task whose candidate spans multiple PRAXIST modules (not one file).
2. A held-out task suite that is not visible during candidate search.
3. A promotion record that links to the operator contract evidence manifest.
4. A second operator (C3) that can reproduce the same boundary and evidence.
5. A capability slope over multiple generations, not one promotion.
