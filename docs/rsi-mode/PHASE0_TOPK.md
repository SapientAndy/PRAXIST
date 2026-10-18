# Phase 0 — Lightweight Top-K Engine Test

**Status:** completed two-generation engine smoke. This is **not RSI** and not a
claim about model-level self-improvement.

## Why this task

The rocket PC task was CPU-feasible but too agent-heavy for a two-peer smoke.
This task is deliberately small and real:

- one candidate file: `workspace/solution.py`;
- a deterministic correctness contract for `top_k(items, k)`;
- a fixed 200,000-integer benchmark;
- a sealed evaluator that copies the candidate to a temp directory;
- a primary metric with headroom:

```text
deterministic_score = correctness_rate * (baseline_median_ms / candidate_median_ms)
```

A baseline-equal implementation scores `1.0`. The task has no GPU dependency and
evaluates in under a second.

## Run configuration

```text
task:        topk_optimization
model:       deepseek-flash
peers:       2
generations: 2
DIG:         disabled
QD:          disabled
evaluator:   evaluations/run.py
```

The run was launched directly through `python -m praxist.run` because the WSL
daemonized launcher was being reaped. Both generation boundaries were written.

## Result

| Generation | Candidate | Score | Evidence | Promotion |
|---|---|---:|---|---|
| Baseline | sort-based `top_k` | 1.000000 | complete | starting parent |
| Gen 0 | `gen0_peer1_bounded_heap` | **16.636780** | complete | 1 promoted |
| Gen 1 | `gen1_peer1_control_champion` | **17.299394** | complete | 1 promoted |

Both generation boundaries exist:

```text
gen_0/generation_boundary.json   promoted_count: 1
gen_1/generation_boundary.json   promoted_count: 1
```

The best final result is generation 1 at **17.30× the baseline score**, with
correctness 1.0 on all seven cases. The improvement is a real algorithmic change
(bounded heap / selection family), not a change to the evaluator or baseline.

## Caveats

- **Gen 0 PI synthesizer failed non-strict:** it produced no agenda after 915 s.
  The boundary still committed and promoted one candidate. This is an
  orchestration defect to fix, not a reason to discard the evidence.
- **Gen 1 PI status:** `skipped_last_generation`, which is expected for the final
  configured generation.
- **Human promotion is not automatic.** The run promoted within its own frontier;
  production promotion remains a separate human gate.
- **Two generations is a smoke, not a capability curve.** It shows the engine can
  produce and carry a better candidate; it does not establish open-ended RSI.
- **Timing noise:** the evaluator uses a 5% noise floor and alternating
  baseline/candidate measurements. The 17× gain is far outside that floor.
- The task is intentionally simple. A harder benchmark is required before using
  the word "weak RSI".

## Takeover validation status

A separate `praxist --takeover --operator codex --task-path ...` attempt was
made after the direct run. It did not reach task initialization: the installed
Codex CLI reports `Not logged in`, so the takeover TUI waited at authentication
and was stopped. No task files were changed by that attempt.

That means the direct run evidence above is valid, but the **guided takeover
path is still unvalidated**. To close that gap, log in to Codex in WSL
(`codex login`) or install/authenticate Claude Code, then rerun the takeover
against the same top-k task. Do not send credentials through chat.

## What this proves

PRAXIST can run a real, multi-generation optimization on a CPU-only task,
evaluate candidates through a task-owned sealed evaluator, promote a better
candidate at a committed generation boundary, and improve again in the next
generation.

That is the engine behavior Phase 0 needed. It is not model-level RSI, and it is
not a production claim.
