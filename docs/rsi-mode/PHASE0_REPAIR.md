# Phase 0 Task-Level Repair — Frozen Hash Alignment

**Date:** 2026-10-18  
**Scope:** the installed `rocket_booster_recovery` example only, not PRAXIST core.  
**Approval:** explicit operator approval for a task-owner harness repair.

## Why a repair was needed

The bundled PC example was internally inconsistent:

- `task_PC/task.yaml` declared task version `2.0.5`;
- `task_PC/evaluations/controller_ood/evaluation.yaml` declared evaluator version
  `2.0.2`;
- the task's `SHA256SUMS` and `task_assets_manifest.json` both recorded
  `src/plant_adapter.py` as `b6a6...`;
- the evaluator's `FROZEN_HASHES` recorded `63f5...`, which matches neither the
  CRLF nor the LF form of the installed file;
- all frozen assets were installed with CRLF line endings, while the evaluator
  hashes raw bytes and expects the LF-normalized hashes.

The canary therefore stopped at the integrity gate before any controller score
was produced.

## What was changed

Backups were written under
`/home/andyl/PraxistExamples/rocket_booster_recovery/_repair_backup/`:

- `plant_adapter.py.orig`
- `evaluator.py.orig`
- `vendor_frozen_c05_plant/` (full frozen vendor tree)

Changes:

1. Normalized all 15 files listed in the evaluator's `FROZEN_HASHES` to LF line
   endings. No source content was otherwise edited.
2. Updated the evaluator's `FROZEN_HASHES` entry for `src/plant_adapter.py`
   from `63f5...` to `b6a6...`, matching the task's `SHA256SUMS` and
   `task_assets_manifest.json`.
3. Did **not** change the controller, plant behaviour, evaluator logic, metrics,
   baseline values, or candidate interface.

After the change, all 15 frozen entries match their files exactly.

## Verification

```text
OK  src/plant_adapter.py b6a68c67bfb8 b6a68c67bfb8
OK  vendor/frozen_c05_plant/config.yaml 80201171ae60 80201171ae60
OK  vendor/frozen_c05_plant/contact_law.py 0d746ba03e34 0d746ba03e34
OK  vendor/frozen_c05_plant/fuel_schedule.py 8032873f7783 8032873f7783
OK  vendor/frozen_c05_plant/gear_frac_candidate.yaml b270d3af8279 b270d3af8279
OK  vendor/frozen_c05_plant/grid_fin_aero.py d2bc0370e904 d2bc0370e904
OK  vendor/frozen_c05_plant/guidance_divert.py 8a3821200c83 8a3821200c83
OK  vendor/frozen_c05_plant/harness/integrator_flags.py 209720ec3b44 209720ec3b44
OK  vendor/frozen_c05_plant/plant_aero.py a8c92998d8ca a8c92998d8ca
OK  vendor/frozen_c05_plant/ppo_rocket_6dof_finned_jax.py e9ff8976c667 e9ff8976c667
OK  vendor/frozen_c05_plant/provenance_labels.py 427722dd8ca0 427722dd8ca0
OK  vendor/frozen_c05_plant/residual_fuel_mask.py 31f73eb40f65 31f73eb40f65
OK  vendor/frozen_c05_plant/residual_mask.py 98aacdc530c9 98aacdc530c9
OK  vendor/frozen_c05_plant/reward_shaping.py 43f5675fbc19 43f5675fbc19
OK  vendor/frozen_c05_plant/terminal_reward.py 668d318bf87b 668d318bf87b
```

## Canary result

Command:

```bash
cd task_PC
XLA_PYTHON_CLIENT_PREALLOCATE=false ../.venv/bin/python \
  evaluations/controller_ood/run.py \
  --variant-dir assets/baseline \
  --mode canary \
  --output-dir experiments/canary_baseline_repaired2 \
  --batch-size 1024
```

Result:

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
proves the evaluator can now load the frozen boundary and execute a rollout on
CPU. It says nothing about the controller's quality, because one unit cannot
support a landing-success estimate.

## What this repair does not do

- It does not change the scientific protocol or metric definition.
- It does not make the task upstream-canonical; it is a local task-level repair.
- It does not produce a baseline; the complete protocol is 13,312 units.
- It does not justify calling anything RSI.

## Next

Choose one:

1. Run `development` (2,048 units) on CPU for a bounded baseline candidate; at
   roughly the canary's per-unit cost this is a multi-hour run and must be
   budgeted, not assumed.
2. Run the complete protocol on a GPU host; the example's intended PC/GPU
   qualification path expects a proper baseline measurement.
3. Use a lighter standard task to validate PRAXIST's multi-generation engine
   before spending hours on the rocket baseline.
