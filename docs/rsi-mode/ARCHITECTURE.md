# PRAXIST-RSI Mode: Architecture RFC v0.1

**Status:** draft for discussion. No implementation, no RSI claim.

## 1. Summary

PRAXIST is a multi-generation research engine whose task project owns the
objective, evaluator, metrics, and candidate code. RSI mode changes one thing:
the candidate code is a **copy of the system**. The engine still runs the same
research loop; the object of optimization is now the system's own implementation.

The mode is only credible if three separations hold:

1. **Candidate vs kernel.** The candidate can change its own package, but not
   the running orchestrator, scheduler, sandbox, or lifecycle code.
2. **Candidate vs evaluator.** The candidate cannot write tests, scores,
   baselines, or the evaluator. The evaluator runs from a read-only tree.
3. **Candidate vs promotion.** The candidate cannot approve itself. Promotion
   records are append-only and require an independent gate.

If any separation fails, the loop still produces code changes, but its score is
no longer evidence of improvement.

## 2. Definitions

| Term | Meaning |
|---|---|
| **Kernel** | The smallest trusted PRAXIST process that schedules peers, enforces sandboxes, writes run records, and closes generations. |
| **Candidate** | A complete, importable copy of the system under test. Peers may edit only this tree. |
| **Evaluator** | A sealed benchmark plus scorer that maps a candidate to structured metrics. It is read-only to the candidate. |
| **Promotion record** | An append-only record of a candidate version, its score, protocol status, diff, and approval decision. |
| **Parent** | The candidate version from which the next generation starts. |
| **Generation** | One mutation → evaluation → selection round. |
| **Weak RSI** | Repeated, independently measured improvement across generations, with a human or independent promotion gate. |
| **Self-repair** | Restoring a degraded candidate to a known baseline. This is not RSI. |

## 3. Ownership boundary v2

The existing boundary is:

> Task project owns objective, baseline, evaluator, metrics, roles, prompts,
> assets. It must not own Praxist source or another task's state.

The proposed boundary is:

| Root | Candidate access | Owner | Notes |
|---|---|---|---|
| `kernel/` | read-only | trusted operator | Frozen for the run; changes require a new kernel release. |
| `candidate/` | read-write | candidate | Only this tree may be edited by peers. |
| `evaluator/` | read-only | independent evaluator owner | Tests, scorer, fixtures, held-out data. |
| `promotions/` | append-only | promotion gate | Candidate may not write or delete records. |
| `runs/` | append-only | kernel | Immutable run artifacts, logs, and lineage. |
| `policies/` | read-only | operator | Resource, network, and safety limits. |

The candidate may **read** the evaluator interface and public test names if the
benchmark is white-box. It may not write to the evaluator tree. Held-out tests
remain outside the checkout and are mounted only during scoring.

## 4. Components

### 4.1 Kernel

- Starts and stops a run.
- Materializes the candidate sandbox from a version tag.
- Injects only the candidate path into the peer environment.
- Mounts `kernel/`, `evaluator/`, `promotions/`, and `runs/` read-only.
- Enforces network, CPU, memory, wall-clock, and process limits.
- Writes a run manifest with hashes of kernel, evaluator, candidate, and policy.
- Closes the generation only after the evaluator returns a signed summary.

### 4.2 Candidate

- A complete copy of the system package, including its own tests if useful.
- Peers may change code, prompts, roles, memory policy, and orchestration logic
  inside the candidate tree.
- The candidate may add its own tests, but those tests are not the score.
- The candidate may not import or modify the kernel/evaluator/promotion trees.

### 4.3 Evaluator

- A separate repository or read-only mount.
- Exposes exactly one public command, for example `run.py`.
- Copies the candidate to a throwaway directory and runs the sealed suite with
  a clean environment.
- Emits a structured summary with metric names, directions, values, protocol
  status, maturity, and the candidate version.
- Never imports the candidate in the evaluator process.
- Records the hashes of the tests and fixtures used for the score.

### 4.4 Promotion gate

- Receives the evaluator summary and candidate diff.
- Rejects candidates with protocol violations, missing baselines, or score
  regressions.
- Requires an independent human or service approval.
- Writes one append-only promotion record.
- Tags the approved candidate as the next parent.
- Keeps rejected candidates as diagnostic evidence, not as parents.

## 5. Task contract changes

A standard PRAXIST task keeps its current `task.yaml` contract. RSI mode adds a
mode-level block, not task-specific facts:

```yaml
rsi_mode:
  enabled: true
  candidate_root: candidate
  kernel_root: kernel
  evaluator_root: evaluator
  promotion_root: promotions
  run_root: runs
  candidate_version: rsi-v0
  parent_version: null
  writable_roots:
    - candidate
  read_only_roots:
    - kernel
    - evaluator
    - promotions
    - runs
  promotion:
    require_human_approval: true
    require_protocol_pass: true
    require_score_improvement: true
```

The block is intentionally declarative. The kernel, not the candidate, enforces
it. A task project that asks for a writable evaluator is rejected at resolve
time.

## 6. Evaluation contract

### 6.1 Metrics

Every metric that can affect promotion must declare:

- name;
- direction (`maximize` or `minimize`);
- baseline value and baseline provenance;
- whether it is a primary, secondary, or diagnostic metric;
- the evidence stage at which it is considered mature.

At least one metric must have **headroom**. A task that only restores a known
baseline measures repair, not improvement.

### 6.2 Sealed suite

- The evaluator copies the candidate to a temp directory.
- The sealed tests and scorer are outside the candidate.
- The candidate cannot edit, skip, or delete tests.
- The evaluator checks the test manifest hash before and after the run.
- The evaluator rejects candidates that modify test discovery, import paths, or
  the scoring process.
- Held-out tests are used for the promotion decision when available.

### 6.3 Protocol integrity

A score is only eligible for promotion if:

- the evaluator completed;
- the expected number of tests ran;
- no test was skipped or deleted;
- the candidate did not change the evaluator, baseline, or protocol files;
- the candidate's diff is limited to writable roots;
- the run manifest hashes match the frozen kernel and evaluator.

Any violation produces `protocol_pass: false` regardless of score.

## 7. Promotion and rollback

### 7.1 Promotion conditions

A candidate becomes the next parent only if all are true:

1. `protocol_pass == true`;
2. primary metric improves over the parent by at least the declared minimum
   effect;
3. secondary metrics do not cross their declared guardrails;
4. the diff is reviewable and contains no secrets;
5. an independent approver signs the promotion record.

### 7.2 Promotion record

Each record contains:

- candidate version and parent version;
- generation number;
- metric values and direction;
- baseline and parent scores;
- evaluator manifest hash;
- candidate diff hash;
- protocol status and failure reasons;
- approver identity and timestamp;
- decision (`promote`, `reject`, `hold`);
- human-readable notes.

The record is append-only. Corrections are new records; old records are never
rewritten.

### 7.3 Rollback

- Every promoted version is a tag or commit in the candidate repository.
- The kernel can start a run from any promoted tag.
- A regression or safety incident rolls back to the last known-good tag.
- Rollback is a new run record, not a deletion of history.

## 8. Generation loop

```text
v0 baseline
  → peers mutate candidate
  → kernel builds sandbox
  → evaluator scores candidate
  → promotion gate decides
  → v1 = approved candidate or v0
  → next generation starts from v1
```

The loop is deliberately conservative:

- no promotion without a score and protocol record;
- no parent change without human approval;
- no deletion of failed candidates;
- no change to the evaluator during a generation;
- no silent retry that changes the evidence cutoff.

## 9. Safety and anti-gaming

| Risk | Control |
|---|---|
| Candidate edits tests or scorer | Read-only evaluator mount; hash checks; diff allowlist. |
| Candidate fakes metrics | Evaluator owns the score; candidate output is never trusted as a metric. |
| Candidate imports kernel state | Clean environment; candidate path only; no kernel imports. |
| Candidate adds network or credentials | Network off by default; credential scan; dependency allowlist. |
| Candidate overfits visible tests | Held-out tests for promotion; multiple seeds; generalization check. |
| Candidate changes promotion logic | Promotion tree read-only; append-only records; independent approver. |
| Run escapes sandbox | Resource limits; process group kill; no host mounts; audit log. |
| Capability drift | Human review of diff; guardrail metrics; rollback tags. |
| License or supply-chain issue | Dependency review; license review before commercialization. |

## 10. Phased plan

### Phase 0 — Validate the engine, not RSI

Use a standard PRAXIST task from a writable example. Run the guided `takeover`
path with two or three generations. Record the generation scores. This answers:
does PRAXIST's ordinary multi-generation optimization work on this host?

**Exit:** a reproducible baseline, a completed generation boundary, and a
monotonic or explainable score curve.

### Phase 1 — One controlled self-repair generation

Use a candidate copy, an external evaluator, and one generation. This is the
experiment already prototyped: a degraded candidate is repaired to the clean
baseline. It proves the measurement layer and the sandbox, not RSI.

**Exit:** start score, repaired score, zero protocol violations, reviewed diff.

### Phase 2 — Versioned promotion over multiple generations

Add version tags, promotion records, rollback, and a task with headroom. Run at
least three generations from the best approved parent. Measure whether the
score improves across generations.

**Exit:** at least three generations; every promotion has a record; the score
curve is not flat; rejected candidates remain visible.

### Phase 3 — Held-out self-benchmark

Move the promotion decision to held-out tasks or held-out tests. Check whether
improvements generalize beyond the visible benchmark. Add multiple seeds and a
cost/latency guardrail.

**Exit:** held-out improvement; no protocol violations; reproducible curve.

Only after Phase 3 should the project use the phrase **weak RSI** in external
material.

## 11. Acceptance criteria for “weak RSI”

A run may be called weak RSI only if:

- at least three generations were evaluated;
- the primary metric improved on a held-out evaluation;
- the improvement is larger than the declared noise floor;
- no candidate modified the evaluator, kernel, or promotion record;
- every promoted version has a human or independent approval;
- the full lineage is reproducible from tags and manifests;
- the result survives a rollback-and-replay check.

Anything less is self-repair, automation, or a promising prototype.

## 12. Open questions

1. **What is the “self”?** Code only, or also prompts, roles, memory policy,
   orchestration, and tool selection? The first implementation should start with
   code and prompts; orchestration changes are higher risk.
2. **How white-box is the evaluator?** Visible tests help repair; held-out tests
   help measure generalization. The mode should support both and make the
   distinction explicit in the score record.
3. **What counts as a new capability?** Restoring a baseline is not improvement.
   The benchmark needs a metric with headroom, or a held-out task that the
   parent cannot solve.
4. **Who approves promotions?** A human is the default. An independent service
   is acceptable only if it is outside the candidate's writable surface and
   itself audited.
5. **How much compute per generation?** Multi-agent research is expensive. A
   generation budget and a cost-per-improvement metric are required before
   long runs.
6. **What is upstreamable?** The kernel/evaluator split and promotion record may
   be useful to upstream PRAXIST; the self-modification mode itself should remain
   a fork until the safety model is proven.

## 13. Non-goals

- Model-weight self-training.
- Autonomous objective selection.
- Automatic production deployment.
- Letting the candidate modify its own evaluator.
- Claiming RSI from a single repair or a single generation.
