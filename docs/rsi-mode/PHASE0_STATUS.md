# Phase 0 Status — Canary Unblocked After Task-Level Repair

**Date:** 2026-10-18  
**Host:** WSL Ubuntu, Python 3.12, CPU-only (`jax.devices() == [CpuDevice(id=0)]`)  
**Claim:** no baseline score, no capability result, no RSI claim.

> **Update:** with explicit operator approval, the task-level hash repair
> described in [`PHASE0_REPAIR.md`](PHASE0_REPAIR.md) was applied. All 15 frozen
> assets now match, and the one-unit canary completes on CPU. The canary is
> still not a baseline or a capability result.

## What was done

1. Installed the writable example:

   ```bash
   praxist examples install rocket_booster_recovery \
     --destination /home/andyl/PraxistExamples/rocket_booster_recovery
   ```

2. Created a task-local `.venv` and installed the PC requirements with CPU JAX:

   ```text
   jax==0.9.2  numpy==2.4.6  scipy==1.17.1  matplotlib==3.11.1  PyYAML==6.0.3
   ```

   `jax.devices()` returned `[CpuDevice(id=0)]`. No CUDA device is present.

3. Resolved the PC task:

   ```bash
   praxist resolve task_PC --run-dir /tmp/rocket_resolve
   ```

   Result: `status: resolved`, with a warning that `task.yaml` declares no
   baselines while `assets/baselines/results.jsonl` exists. The warning is
   expected for this example: its README says the PC baseline has not been
   measured and `task.yaml:baselines` is intentionally empty.

4. Ran the one-unit canary against the frozen baseline:

   ```bash
   cd task_PC
   XLA_PYTHON_CLIENT_PREALLOCATE=false ../.venv/bin/python \
     evaluations/controller_ood/run.py \
     --variant-dir assets/baseline \
     --mode canary \
     --output-dir experiments/canary_baseline \
     --batch-size 1024
   ```

## Result before repair

The first canary did **not** produce a controller score. It stopped at the
evaluator's frozen-asset integrity gate:

```text
status: protocol_failed
error: frozen asset hash mismatch: src/plant_adapter.py;
expected 63f543e2125b367cf7672360984167f0c99c83362e4259bbcb301a8e0650101f,
got     42f8b1a031f33a4cf7f419ae0dc04fd26a7fda5a41a13270ef7bde8c3966aa20
```

The installed file had CRLF line endings. Its LF-normalized SHA-256 was
`b6a68c67bfb87ebc708747fe708fc8ae80a00242c2225e1fe3ada1600bf8cd62`, which is
exactly the value in the example's `SHA256SUMS` and in
`task_PC/assets/task_assets_manifest.json`. The evaluator's hard-coded
`FROZEN_HASHES` entry expected a third value, `63f5...`, which did not match
either the CRLF or LF form of the installed asset.

A full comparison of the evaluator's 15 frozen entries against the installed
files found only this one hash mismatch. The other 14 entries matched their
LF-normalized files. That pointed to a stale hash entry for
`src/plant_adapter.py`, not a broad asset-corruption problem.

This was a **task-packaging inconsistency**, not a controller failure and not a
PRAXIST orchestration failure. The frozen evaluator was doing its job by
refusing to score a candidate whose immutable boundary did not match its own
attestation.

## Repair applied

With explicit operator approval, the task-level repair in
[`PHASE0_REPAIR.md`](PHASE0_REPAIR.md) was applied:

- backed up the original `plant_adapter.py`, evaluator, and frozen vendor tree;
- normalized all 15 frozen assets to LF line endings;
- changed the evaluator's `FROZEN_HASHES` entry for `src/plant_adapter.py` from
  `63f5...` to the manifest value `b6a6...`;
- did not change the controller, plant behaviour, metrics, baseline values, or
  evaluator logic.

All 15 frozen entries now match their files exactly.

## Canary result after repair

```text
result_status: canary
actual_evaluation_units: 1
required: 13312
complete_eval: false
landing_success_rate: 0.0
first_contact_sink_speed_p95_mps: 41.868
elapsed_seconds: 3.844
jax_backend: cpu
```

This is a **one-unit canary**, not a baseline and not a capability result. It
shows that the evaluator can now load the frozen boundary and execute a rollout
on CPU. It does not support a landing-success estimate, because one unit cannot
estimate a rate.

## Decision

The task example is locally repaired and usable for a bounded Phase 0 run, but
it remains a **task-level repair**, not an upstream-canonical example. Before a
multi-generation Phase 0 run, choose a budget:

- `development` = 2,048 units; on CPU this is a multi-hour run;
- `complete` = 13,312 units; on CPU this is not practical without a long
  unattended window;
- a GPU host is the intended path for the complete protocol.

Do not treat the canary's `landing_success_rate: 0.0` as a baseline. It is one
unit.

## What this does not tell us

- It does not tell us whether the rocket controller is good or bad.
- It does not tell us whether PRAXIST's generation loop works.
- It does not justify skipping Phase 0 or substituting a self-repair sandbox
  result for a standard-task result.

The next valid step is to fix the example packaging or choose a standard task
whose frozen assets and evaluator hashes are already consistent.
