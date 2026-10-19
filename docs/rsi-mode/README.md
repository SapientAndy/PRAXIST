# PRAXIST-RSI Mode (RFC)

**Status: design draft plus an executable promotion prototype. This branch makes no full-RSI claim.**

This directory describes a proposed operating mode in which a PRAXIST run's
research object is a **candidate copy of the system itself**, while the
orchestration kernel, the evaluator, and the promotion record remain outside the
candidate's writable surface.

The goal is not to remove PRAXIST's ownership boundary. The goal is to replace

> a task project must not own Praxist source

with a narrower, auditable rule:

> a **candidate** may own a copy of the system source, but it may not own the
> **kernel**, the **evaluator**, or the **promotion record**.

That distinction is the whole design. A system that can rewrite its code and
also rewrite its judge is not self-improving; it is self-dealing.

## Why this mode exists

PRAXIST already supplies the hard part of a research loop:

- parallel peers and PI/Chair synthesis;
- task-owned evaluation and baseline provenance;
- durable evidence, frontier/incubator state, and generation boundaries;
- replay, resume, and audit artifacts;
- plugin boundaries for runtimes, providers, tools, roles, and workflows.

What PRAXIST deliberately does **not** supply is a supported way for the
research object to be PRAXIST itself. The current ownership boundary forbids a
task project from owning Praxist source. This RFC defines the smallest
controlled exception that can be measured safely.

## Proposed layout

```text
praxist-rsi/
├─ kernel/           # frozen orchestration + sandbox + lifecycle
├─ candidate/        # mutable system copy; peers edit only here
├─ evaluator/        # read-only sealed benchmark + scorer
├─ promotions/       # append-only version records and approvals
├─ runs/             # immutable run artifacts and lineage
└─ policies/         # resource, network, and promotion policy
```

The existing PRAXIST task project remains the unit of configuration. The new
mode adds a **mode-level contract** that decides which roots are writable and
which roots are mounted read-only for the candidate.

## Non-goals

- This is not model-level RSI. Model weights are not trained or edited.
- This is not autonomous goal setting. The objective, metric, baseline, and
  launch authorization remain human inputs.
- This is not automatic production promotion. A human or an independent
  promotion service approves every version that becomes the next parent.
- This is not a claim that one self-repair generation equals RSI.

## Documents

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — components, ownership boundary v2,
  evaluation contract, promotion loop, safety rules, and phased plan.
- [`PHASE0.md`](PHASE0.md) — plan for validating PRAXIST's ordinary
  multi-generation optimization before building RSI mode.
- [`PHASE0_STATUS.md`](PHASE0_STATUS.md) — what happened when the plan was
  tried on the PC example: a frozen-asset hash mismatch blocked the canary, so
  no score was produced.
- [`PHASE0_REPAIR.md`](PHASE0_REPAIR.md) — the approved task-level repair:
  LF normalization, hash alignment, and the one-unit canary result.
- [`PHASE0_TOPK.md`](PHASE0_TOPK.md) — the lightweight two-generation engine
  test with a real top-k optimization task: baseline 1.0 → gen0 16.64 → gen1
  17.30.
- [`PHASE1_REDACTION.md`](PHASE1_REDACTION.md) — the first subsystem-level
  self-improvement task: PRAXIST's redaction layer under a sealed correctness
  and throughput evaluator.
- [`PHASE1_REVIEW.md`](PHASE1_REVIEW.md) — the external differential audit that
  found cross-line redaction gaps in the fast candidates and blocked promotion.
- [`PHASE1B_REDACTION_V2.md`](PHASE1B_REDACTION_V2.md) — continuation from the
  safe `span_slice` parent: 29/29, 14.90 ms → 4.49 ms, 3.3190 relative, external
  fuzz 0/1,200.
- [`PHASE1C_REDACTION_V3.md`](PHASE1C_REDACTION_V3.md) — continuation from the
  gated v2 winner: 29/29, 4.49 ms → 2.87 ms, 1.5630 relative, external fuzz
  0/1,200.
- [`PHASE1D_REDACTION_V4.md`](PHASE1D_REDACTION_V4.md) — continuation from the
  v3 gateskip winner: 29/29, 2.87 ms → 1.75 ms, 1.6456 relative, external fuzz
  0/1,200.
- [`PHASE1E_REDACTION_V5.md`](PHASE1E_REDACTION_V5.md) — continuation from the
  v4 spanmerge winner: 29/29, 1.75 ms → 1.40 ms, 1.2498 relative, external fuzz
  0/1,200.
- [`PHASE2_HELDOUT.md`](PHASE2_HELDOUT.md) — held-out audit: exactness passes;
  67–68× on benchmark-shaped seeds, 16–138× across density, ~1× on long-line
  shapes.
- [`PHASE3_KERNEL.md`](PHASE3_KERNEL.md) — kernel-copy task: any module in a
  full PRAXIST copy is writable; peer0 4.86×, 54/55, fuzz 0, held-out 4.7–5.0×
  on benchmark shapes and 1.15–1.18× on long-line shapes.
- [`PHASE3B_NAMED_HINT.md`](PHASE3B_NAMED_HINT.md) — named-secret `str.find`
  fast path: 18.52 ms → 10.19 ms, 1.817×, 54/55, fuzz 0.
- [`PHASE3C_LITERAL_SPAN.md`](PHASE3C_LITERAL_SPAN.md) — literal-span fast
  path: 10.19 ms → 6.92 ms, 1.472×, 54/55, fuzz 0, canonical frontier capture
  works.
- [`PHASE3D_FUSED_LITERAL.md`](PHASE3D_FUSED_LITERAL.md) — fused-literal fast
  path: 6.92 ms → 5.63 ms, 1.229×, 54/55, fuzz 0, held-out 11.6–23.0× on
  benchmark shapes and 1.38–1.46× on long-line shapes.
- [`PHASE3E_FASTGATE.md`](PHASE3E_FASTGATE.md) — fastgate: 5.63 ms → 5.20 ms,
  1.083×, 54/55, fuzz 0; current best kernel-copy candidate; stopped when the
  absolute gain fell to 0.43 ms.
- `../../rsi_mode/` — executable promotion recorder and score-curve renderer.
  The recorder refuses correctness failures, duplicate candidates, and approved
  scores that do not improve on the best approved score; approval is explicit.
- [`ownership_boundary.yaml`](ownership_boundary.yaml) — machine-readable
  design contract for writable and read-only roots.
- [`promotion_record.schema.json`](promotion_record.schema.json) — append-only
  record for every candidate that is considered for promotion.

## First milestone

Run a **standard** PRAXIST task through the guided `takeover` path and measure
two or three generations. That establishes whether PRAXIST's ordinary
generation-to-generation optimization works on this host. RSI-mode work starts
only after that baseline is understood; otherwise a failure in the meta-task
cannot be distinguished from a failure in the engine.

The first takeover-style launch was accepted in configured-provider mode
(`praxist start`, DeepSeek API, `agent_runtime:claude_sdk`). Its detached child
was reaped by the WSL launcher, so the measured runs use the equivalent direct
`python -m praxist.run` path. The top-k two-generation result remains the
engine-level evidence; the redaction task is the first candidate-level
self-improvement attempt.
