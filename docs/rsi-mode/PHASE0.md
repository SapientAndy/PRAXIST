# Phase 0 — Validate PRAXIST Itself

**Status: plan only. Not run on this branch yet.**

Before RSI-mode is implemented, establish that PRAXIST's ordinary
generation-to-generation optimization works on a standard task. Otherwise a
failure in the meta-task cannot be separated from a failure in the engine.

## Task choice

Use a writable example with:

- a measurable primary metric and a known direction;
- a baseline that runs without PRAXIST;
- a runtime short enough for two or three generations;
- no dependency on a private dataset or unavailable hardware.

`rocket_booster_recovery` is the default candidate. If its runtime is too heavy
for the host, use a smaller example or the `toy_math` task template for a smoke
run, but do not present the smoke run as a capability result.

## Procedure

1. Install the example into a writable location outside the PRAXIST checkout:
   `praxist examples install rocket_booster_recovery`.
2. Open the installed project and invoke the guided takeover path:
   `praxist --takeover --task-path <installed-project>`.
   If the agent CLI is unavailable, use the `praxist-task-initialization` flow,
   then `praxist resolve` and `praxist doctor` before `start`.
3. Use a short, explicit budget: 2 peers, 2–3 generations, and a wall-clock or
   cost cap appropriate to the task.
4. Record:
   - task path and run ID;
   - baseline metric and provenance;
   - every generation's primary metric;
   - generation boundary completion;
   - protocol failures and rejected candidates;
   - total cost and wall-clock time.
5. Stop after the agreed generations. Do not extend the run mid-flight to chase
   a preferred result.

## Acceptance

Phase 0 passes only if:

- the baseline is reproducible;
- the run completes at least two generation boundaries;
- the primary metric is measured for each generation;
- the score curve is monotonic or has an explainable, evidence-backed reason;
- no evaluator or task file is edited during the run;
- the result can be replayed from the run directory.

A flat curve is a valid result. It means the engine did not improve this task
under this budget; it is not a reason to change the metric after the fact.

## What this phase does not prove

- It does not prove RSI.
- It does not test self-modification.
- It does not justify copying PRAXIST source into a task project.

Its only job is to establish the engine's ordinary multi-generation behavior on
this host.
