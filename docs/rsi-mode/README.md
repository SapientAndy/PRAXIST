# PRAXIST-RSI Mode (RFC)

**Status: design draft. Not implemented. This branch makes no RSI claim.**

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
- [`ownership_boundary.yaml`](ownership_boundary.yaml) — machine-readable
  design contract for writable and read-only roots.
- [`promotion_record.schema.json`](promotion_record.schema.json) — append-only
  record for every candidate that is considered for promotion.

## First milestone

Before this mode is implemented, run a **standard** PRAXIST task through the
guided `takeover` path and measure two or three generations. That establishes
whether PRAXIST's ordinary generation-to-generation optimization works on this
host. RSI-mode work starts only after that baseline is understood; otherwise a
failure in the meta-task cannot be distinguished from a failure in the engine.
