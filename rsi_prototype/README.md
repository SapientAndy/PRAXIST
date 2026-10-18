# PRAXIST self-improvement prototype (branch: `rsi-prototype`)

**Status: measurement scaffold. This is not RSI, and the branch makes no RSI claim.**

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

| Metric | Value |
|---|---|
| Tests | 55 |
| Passed | 54 |
| Failed | 1 |
| Pass rate | **0.9818** |
| Runtime | ~2.4 s |

The single failure is `test_fake_panel_writes_replayable_run_dir` (`Required plugin not found: agent_runtime:fake_runtime`). It is a bundled-plugin discovery issue in the isolated copy, not a candidate regression. It is excluded from the "headroom" discussion below.

## What this proves

- A candidate copy can be scored against tests it cannot edit.
- The evaluator is deterministic, fast, and cheap enough to run every generation.
- The candidate workspace is cleanly separated from the scorer.

## What this does **not** prove

- No model-driven mutation has run yet.
- No generation-over-generation improvement has been shown.
- PRAXIST's own suite is already green (54/54 excluding the plugin issue), so **test pass rate has no headroom**. A real self-improvement task needs a metric with headroom.

## Candidate objectives (pick one before launching)

1. **Self-repair (recommended first):** inject a documented bug set into `workspace/praxist`; baseline drops below 100%; the loop must restore the sealed tests without touching them. Measures fix rate, not capability growth.
2. **Performance:** keep the sealed correctness suite green, maximize a stable throughput/latency benchmark on one core component (e.g. replay verification or redaction). Measures a real capability gain, but needs a low-noise benchmark.
3. **Capability:** add a new sealed feature benchmark (e.g. a CLI contract) not present in the baseline. Closest to real self-improvement, hardest to design fairly.

Recommendation: start with **self-repair** for one generation to validate the loop mechanics, then switch to **performance** for the compounding curve.

## Minimal next milestone

1. Inject 5 documented bugs into `workspace/praxist`; verify each is caught by the sealed tests.
2. Re-run the evaluator; record the degraded baseline.
3. Create `task.yaml` for the meta-task; launch one generation with 2 peers and a fixed budget.
4. Compare generation 1 against baseline; promote only after human review.
5. Record the capability-vs-generation curve. If it is flat, this is automation, not RSI.

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
