# PRAXIST self-improvement prototype (branch: `rsi-prototype`)

**Status: one-generation self-repair demonstrated under a sealed evaluator. This is still not RSI, and the branch makes no RSI claim.**

This branch exists to answer one question with evidence: can a PRAXIST research run improve a copy of PRAXIST itself under a sealed evaluator, with human-controlled promotion?

## What is here

```
rsi_prototype/
├─ workspace/praxist/        # disposable copy of the package the loop may edit
├─ sealed_tests/             # tests copied outside the workspace; candidate cannot edit them
├─ evaluations/run.py        # copies candidate to temp, runs sealed tests, emits JSON
└─ assets/baselines/         # measured baseline
```

The evaluator never imports the workspace directly. It copies `workspace/praxist` into a throwaway directory, prepends that directory to `PYTHONPATH`, and runs the sealed tests against the copy. The candidate can change its own package; it cannot change the tests or the scorer.

## Measured baseline

Environment: WSL Ubuntu, Python 3.12, `pytest` 8.x, 2026-10-18.

| Metric | Clean baseline | Degraded v1 (4 injected bugs) |
|---|---|---|
| Tests | 55 | 55 |
| Passed | 54 | 50 |
| Failed | 1 | 5 |
| Pass rate | **0.9818** | **0.9091** |
| Runtime | ~2.4 s | ~2.2 s |

The single clean-baseline failure is `test_fake_panel_writes_replayable_run_dir` (`Required plugin not found: agent_runtime:fake_runtime`). It is a bundled-plugin discovery issue in the isolated copy, not a candidate regression, and it is out of scope for this task. The maximum achievable score is therefore **54/55**.

`assets/baselines/baseline.json` is the clean measurement; `assets/baselines/degraded_v1.json` is the starting state for the self-repair experiment.

## Run result (2026-10-18)

One generation, two peers, DeepSeek-V4.1-Flash (`deepseek-flash`), sealed evaluator.

| Stage | Passed / total | pass_rate | In-scope failures |
|---|---:|---:|---:|
| Clean baseline | 54 / 55 | 0.9818 | 0 |
| Degraded start | 50 / 55 | 0.9091 | 4 |
| Repaired candidate | **54 / 55** | **0.9818** | **0** |

The accepted peer candidate changed three files under `workspace/praxist` and restored all four failing contracts: reasoning-policy defaults, lossless memory limits, canonical-vs-derived artifact semantics, and latest-generation provenance. It did not touch the sealed tests or the evaluator. Full evidence is in the Desktop report `Hermes 输出/PRAXIST_RSI_Prototype_v1/RUN_REPORT.md`.

Caveat: the PRAXIST orchestrator process exited before writing a final `run_summary.json`. The candidate variant was recovered from the run's `variants/` directory and re-scored with the same sealed evaluator; the 54/55 result is the evaluator's output, not the agent's self-report.

The sealed suite now carries `sealed_tests/fixtures/toy_math/`. One test previously resolved `templates/tasks/toy_math/task.yaml` via the repository layout, so it was not hermetic once the task project moved outside the checkout. That was a harness bug, not a candidate failure.

## Bug set v1

Four deterministic regressions are injected into `workspace/praxist` (see `BUGSET.md`). The sealed tests catch all four: reasoning-policy defaults, artifact semantics, generation provenance, and lossless memory limits. The task is to restore the clean baseline without editing the sealed tests or the evaluator.

> **Do not copy `BUGSET.md` or this README into a live task project.** They name the exact files and changes, so a candidate that can read them gets the answer key. The runnable task project should contain only `task.yaml`, `description.md`, `prompt_task.jinja2`, `README.md` (the neutral `TASK_README.md`), `roles/`, `workspace/`, `sealed_tests/`, `evaluations/`, and `assets/`. Keep `BUGSET.md` in the branch documentation, outside the candidate's readable tree.

## What this proves

- A candidate copy can be scored against tests it cannot edit.
- The evaluator is deterministic, fast, and cheap enough to run every generation.
- The candidate workspace is cleanly separated from the scorer.
- A model-driven peer repaired all four injected regressions and reached the clean baseline (54/55) in one generation, without touching the sealed tests or the scorer.

## What this does **not** prove

- No generation-over-generation improvement has been shown. One repair is not a compounding curve.
- The objective, sealed tests, and baseline are still human-supplied; the loop did not set its own goal.
- Promotion is still human-gated; the run did not promote itself to production.
- The orchestrator process exited before writing a final finding; the candidate was recovered from `variants/` and re-scored. The closed loop's last mile is not yet automatic.
- The self-repair task has no headroom left at 54/55. A real capability-growth experiment needs a metric with headroom.

## Candidate objectives (pick one before launching)

1. **Self-repair (recommended first):** inject a documented bug set into `workspace/praxist`; baseline drops below 100%; the loop must restore the sealed tests without touching them. Measures fix rate, not capability growth.
2. **Performance:** keep the sealed correctness suite green, maximize a stable throughput/latency benchmark on one core component (e.g. replay verification or redaction). Measures a real capability gain, but needs a low-noise benchmark.
3. **Capability:** add a new sealed feature benchmark (e.g. a CLI contract) not present in the baseline. Closest to real self-improvement, hardest to design fairly.

Recommendation: start with **self-repair** for one generation to validate the loop mechanics, then switch to **performance** for the compounding curve.

## Minimal next milestone

1. [x] Inject 4 documented bugs into `workspace/praxist`; verify each is caught by the sealed tests.
2. [x] Re-run the evaluator; record the degraded baseline (50/55, 0.9091).
3. [x] Create `task.yaml` for the meta-task; launch one generation with 2 peers and a fixed budget.
4. [x] Compare generation 1 against baseline (54/55, 0.9818); promotion remains human-gated.
5. [ ] Record the capability-vs-generation curve over a task with headroom. If it is flat, this is automation, not RSI.

## Safety rules for this branch

- The original `praxist/` package is never edited by the loop; only `rsi_prototype/workspace/praxist`.
- The sealed tests and `evaluations/run.py` are outside the candidate's writable surface.
- No automatic promotion to production. A human approves every merge.
- No deployment, no network access from the candidate, no credentials in the workspace.

## Run

```bash
python evaluations/run.py --json-out assets/baselines/baseline.json
```

Requires Python 3.11+ with `pytest`. On this machine:

```bash
/tmp/praxist-venv/bin/python evaluations/run.py
```
