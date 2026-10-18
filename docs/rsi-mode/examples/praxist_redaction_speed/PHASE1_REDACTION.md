# Phase 1 — PRAXIST Redaction Subsystem

**Status: run in progress. This document reports measured results; it does not
claim full PRAXIST RSI.**

## Question

Can PRAXIST's research loop improve a real PRAXIST subsystem while an external
sealed evaluator prevents the candidate from changing the rules?

This is the first candidate-level self-improvement task after the top-k engine
test. It is narrower than "make PRAXIST itself self-improving": the candidate is
one security-critical module, not the whole kernel.

## Task design

- **Candidate:** `workspace/redaction.py`, a copy of
  `praxist/core/redaction.py`.
- **Writable surface:** `workspace/` only.
- **Frozen surface:** `evaluations/`, `sealed_tests/`, `assets/`, `task.yaml`.
- **Sealed correctness:** 23 golden cases covering bearer tokens, OpenAI-style
  keys, GitHub tokens, named secrets, nested JSON, unicode, empty input, clean
  text, and near-miss strings. Outputs and hit classes must match exactly.
- **Benchmark:** deterministic mixed corpus of 945,159 characters, about 90%
  benign lines and 10% secret-bearing lines; median of three runs after one
  warmup, CPU-only.
- **Primary metric:**

  ```text
  deterministic_score = correctness_rate * (baseline_median_ms / candidate_median_ms)
  ```

- **Baseline:** pristine module, `baseline_median_ms = 100.9227`, correctness
  `23/23`, score `1.0` by construction.
- **Integrity:** `assets/protected_manifest.json` records SHA-256 hashes of the
  evaluator, sealed checks, golden cases, task contract, and baseline.
  `rsi_mode/verify.py` checks them after a run.

## Why this task

The redaction layer is a real PRAXIST component with a clear contract and a
security-relevant failure mode. A faster implementation that silently stops
redacting a token class is a regression, not an optimization. The sealed golden
cases make that trade-off explicit.

The benchmark is deliberately mixed: a cheap literal prefilter can skip
expensive regexes on benign lines, but the candidate still has to preserve
every secret pattern and the exact redaction output.

## Run protocol

- Task project outside the PRAXIST source checkout:
  `/home/andyl/PraxistExamples/praxist_redaction_speed`
- Runtime: DeepSeek API, `agent_runtime:claude_sdk`, `deepseek-flash`.
- Generations: 3; cohort: 2.
- `praxist start` in configured-provider mode accepted the launch
  (`auth_mode: configured-provider`), but the detached child was reaped by the
  WSL launcher. The measured run therefore uses the equivalent direct
  `python -m praxist.run` path.
- Run directory: `experiments/run_redaction_direct_1`.

## Headroom check

A human-authored reference candidate was scored only to prove the task has
headroom and that the evaluator accepts a faster candidate. It is **not**
counted as agent evidence:

```text
23/23 correctness
candidate_median_ms = 24.889
baseline_median_ms  = 100.9227
deterministic_score = 4.054912
```

The reference adds a line-level literal prefilter before the existing regexes.
That confirms the benchmark rewards a real, correctness-preserving optimization
rather than an impossible target.

## Results

The guided run produced a monotonic, sealed, end-to-end score curve on one
PRAXIST subsystem:

| Generation | Candidate | Correctness | Median ms | `deterministic_score` |
|---|---|---|---:|---:|
| baseline | pristine `redaction.py` | 23/23 | 100.9227 | 1.0000 |
| gen 0 | `gen0_peer1_lineprefilter_v2` | 23/23 | 14.4184 | **6.9996** |
| gen 1 | `gen1_peer0_marker_dispatch_v2` | 23/23 | 8.3183 | **12.1326** |

Both candidates were scored by the sealed evaluator after the evaluator copied
the candidate into a temporary directory. The sealed golden cases and
`assets/protected_manifest.json` remained unchanged; `rsi_mode/verify.py`
returned `ok: true` after the runs.

The gen-0 candidate uses one whole-text literal marker pass to locate the
minority of lines that can contain a secret, then applies the original ordered
regex pipeline only to those lines. The gen-1 candidate refines the marker
dispatch and reduces the end-to-end cost from 14.4 ms to 8.3 ms while preserving
23/23 correctness. This is a real throughput gain on the task's benchmark, not a
test edit.

### Failed first attempt

An earlier open-ended version of the run (`run_redaction_open_1`) timed out
before producing a scored candidate: the two peers spent their sessions
profiling and ended with baseline-only findings. The guided prompt added an
explicit 10-minute timebox and a concrete first mechanism; the next run produced
scored candidates in the first generation. That difference is a prompt/task
design effect, not evidence about the PRAXIST engine.

### Differential audit

The 23-case sealed set is too thin for an exactness claim. A separate external
fuzz check compared the gen-1 candidate against the pristine module on 1,200
generated strings, including cross-line markers, duplicate secrets, Unicode, and
near-miss tokens:

```text
cases=1200 output_mismatches=119 hit_only_mismatches=118
```

A concrete failure:

```text
input:  "Bearer \nabcdefghijklmnop"
base:   "<redacted:bearer_token>"
cand:   "Bearer \nabcdefghijklmnop"
```

The baseline's `Bearer\s+` can cross a newline; the line-level prefilter does not
treat a line ending in `Bearer ` as a cross-line risk. Repeated secrets also
produce different hit-list cardinality.

This audit is **not** part of the sealed evaluator and does not change the
recorded scores. It means the 6.9996 and 12.1326 scores are benchmark-specific
throughput results, not proof that the full redaction contract is preserved.
The right response is to reject the candidates until the sealed evaluator
includes cross-line and differential cases.

### Promotion state

Two append-only records are currently `proposed`, not approved:

- gen 0: `6.999577`, candidate SHA-256 `be907da19013...`
- gen 1: `12.132611`, candidate SHA-256 `54367dc52441...`

A human approval is still required before either becomes the parent of a
production branch. The records and the score curve are in `promotions/`.

### What the curve means

This is **subsystem-level self-improvement**: the research loop improved a real
PRAXIST module across generations, under a sealed evaluator, with a monotonic
score and preserved correctness. It is the first measured capability curve in
this prototype.

It is **not full PRAXIST RSI**. The object is one module, not the kernel; the
objective and metric are human-set; the benchmark is synthetic and
in-distribution; and the promotion gate is human. The gen-1 PI agenda explicitly
flagged that the marker prefilter may exploit the benchmark's selectivity and
proposed a falsification arm, which is the right next step rather than a reason
to overclaim.

## What would count as evidence

- A correct candidate (`correctness_rate == 1.0`) with
  `deterministic_score > 1.0` is a measured throughput improvement.
- A monotonic score curve across generations is evidence that the loop can
  compound a capability improvement on this subsystem.
- A flat or negative curve is a valid negative result. It would show that the
  current loop and model did not find a safe optimization, not that RSI is
  impossible.

## What this does not prove

- It does not prove full PRAXIST RSI. The candidate is one module, not the
  kernel/candidate split described in the RFC.
- It does not prove open-ended capability growth. The objective, metric,
  baseline, and promotion gate remain human inputs.
- It does not prove model-level RSI. Model weights are unchanged.
- The benchmark is synthetic and in-distribution. There is no held-out
  benchmark yet, so a positive result is a throughput result, not a general
  capability claim.
