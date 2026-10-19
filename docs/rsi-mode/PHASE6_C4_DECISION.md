# C4 v2 — Decision: Negative Result Accepted

**Date:** 2026-10-19  
**Decision:** Accept the C4 v2 negative result. Do not run C4 v3. Do not promote any C4 candidate.

## Rationale

C4 v1 was invalidated by benchmark memoization. C4 v2 was the anti-cheat rerun, and no candidate passed all gates:

| Candidate | Raw score | Audit result |
|---|---:|---|
| `framecanon` | 1.276144 | empty-list hash mismatch |
| `bincanon` | 1.126823 | 3/1,500 cache fuzz mismatches |
| `hashlean` | 1.026084 | five-run median 0.980815; no stable gain |

The repeated pattern is clear: candidates can improve one module, but not yet produce a **stable, semantically correct, multi-module** gain under external held-out and fuzz. More C4 generations would mostly search the same local design space.

## What is accepted

- C4 is **not passed**.
- No promotion is approved.
- The C4 v1 scores (1.2579 / 345.3) are invalid and must not be cited.
- C4 v2 scores above are retained as audit evidence, not capability claims.

## What this establishes

1. The evaluator can detect benchmark memoization.
2. External fuzz catches semantic regressions that held-out examples miss.
3. Repeated measurement is necessary; single-run frontier scores are not enough.
4. The current bottleneck is evaluator/task design and candidate quality, not PRAXIST's ability to edit code.

## Next gate

Do not proceed to "C4 passed" or "RSI achieved." The next experiment, if any, should be a **kernel-level self-referential task** with:

- candidate = research-loop / kernel modules, not just redaction+cache;
- external, candidate-invisible task suite;
- property-based fuzz and repeated measurement;
- human promotion gate.

Until that exists, the project remains at **subsystem-level RSI prototype**, with C4 closed as a negative result.
