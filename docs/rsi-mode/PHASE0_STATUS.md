# Phase 0 Status — Canary Blocked by Example Hash Mismatch

**Date:** 2026-10-18  
**Host:** WSL Ubuntu, Python 3.12, CPU-only (`jax.devices() == [CpuDevice(id=0)]`)  
**Claim:** no score, no capability result, no RSI claim.

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

## Result

The canary did **not** produce a controller score. It stopped at the evaluator's
frozen-asset integrity gate:

```text
status: protocol_failed
error: frozen asset hash mismatch: src/plant_adapter.py;
expected 63f543e2125b367cf7672360984167f0c99c83362e4259bbcb301a8e0650101f,
got     42f8b1a031f33a4cf7f419ae0dc04fd26a7fda5a41a13270ef7bde8c3966aa20
```

The installed file has CRLF line endings. Its LF-normalized SHA-256 is
`b6a68c67bfb87ebc708747fe708fc8ae80a00242c2225e1fe3ada1600bf8cd62`, which is
exactly the value in the example's `SHA256SUMS` and in
`task_PC/assets/task_assets_manifest.json`. The evaluator's hard-coded
`FROZEN_HASHES` entry expects a third value, `63f5...`, which does not match
either the CRLF or LF form of the installed asset.

This is a **task-packaging inconsistency**, not a controller failure and not a
PRAXIST orchestration failure. The frozen evaluator is doing its job by
refusing to score a candidate whose immutable boundary does not match its own
attestation.

## Decision

Do **not** patch the frozen evaluator hash to force the canary to pass. That
would turn a protocol failure into a false green and would contaminate Phase 0.
The example must first be made internally consistent:

- either ship the `src/plant_adapter.py` whose SHA-256 is `63f5...`, with a
  matching manifest and baseline record;
- or update the evaluator's `FROZEN_HASHES` to the manifest's `b6a6...` value
  and re-attest the full frozen boundary;
- then re-run `resolve`, the canary, and only after that the baseline and
  multi-generation run.

## What this does not tell us

- It does not tell us whether the rocket controller is good or bad.
- It does not tell us whether PRAXIST's generation loop works.
- It does not justify skipping Phase 0 or substituting a self-repair sandbox
  result for a standard-task result.

The next valid step is to fix the example packaging or choose a standard task
whose frozen assets and evaluator hashes are already consistent.
