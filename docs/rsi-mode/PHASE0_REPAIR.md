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

## Complete baseline measurement

After the canary, the baseline controller was measured on the complete protocol:

```text
stage: complete
actual_evaluation_units: 13,312
complete_eval: true
landing_success_rate: 0.040283203125
first_contact_sink_speed_p95_mps: 66.39284057617188
elapsed_seconds: 21.04
jax_backend: cpu
```

The development protocol (2,048 units) measured
`landing_success_rate = 0.02783203125` in 4.97 s. The complete baseline is the
number now declared in `task_PC/task.yaml:baselines` as
`pc_cpu_complete_v1`, and `praxist resolve` no longer warns about an empty
baseline contract.

These are **local task-level measurements** on a CPU-only WSL host, not an
upstream-certified PC or GPU result. They are adequate for a bounded engine
smoke test; they are not a platform qualification.

## PRAXIST engine smoke (2 peers / 2 generations)

A bounded engine smoke was launched after the baseline measurement:

```text
task:        task_PC_smoke (copy of task_PC)
model:       deepseek-flash
peers:       2
generations: 2
DIG:         disabled
QD:          disabled
gen cap:     10 minutes (synthesis max interval)
```

It was stopped after about 17 minutes while still in generation 0. The state at
stop:

```text
current_generation:      0
generations_completed:   0
variants_total:          2
findings_total:          2
variants_above_baseline: 0
best_validation_signal:  landing_success_rate = 0.027832 (development, below baseline)
```

Both variants were baseline reference artifacts. The evaluator results were a
one-unit canary (1 / 13,312) and a development run (2,048 / 13,312); neither was
a complete-protocol result. The PI skeptic explicitly recorded that no validated
landing claim existed because both artifacts were incomplete.

This is a **negative/mechanical result**, not a capability result:

- PRAXIST started, ran the task evaluator, produced findings, and entered PI
  synthesis;
- with 2 peers and a 10-minute generation, it did not produce a complete
  candidate or an above-baseline variant;
- the generation did not close before the run was stopped;
- the result does not show that PRAXIST cannot optimize this task; it shows that
  this budget and cohort were too small for this task.

## What this repair does not do

- It does not change the scientific protocol or metric definition.
- It does not make the task upstream-canonical; it is a local task-level repair.
- It does not produce a platform-qualified PC/GPU baseline; the CPU measurement
  is local evidence, not a hardware certification.
- It does not justify calling anything RSI.

## Next

The local complete baseline is measured (13,312 units, 21 s, CPU), but the
2-peer / 10-minute engine smoke was too small for this task: it produced only
incomplete baseline references and no above-baseline variant.

Choose one:

1. Use a genuinely smaller standard task to validate PRAXIST's multi-generation
   loop before returning to rocket.
2. Run rocket with its intended cohort and generation budget (the task defaults
   are 16 peers / 30 generations; a serious run needs a GPU host and a real
   budget).
3. Keep the rocket task only as the benchmark asset; do not use a 2-peer smoke
   to judge its capability or PRAXIST's optimization ceiling.
