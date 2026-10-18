# PRAXIST Redaction Throughput

This is a PRAXIST self-improvement task for one security-critical subsystem of
PRAXIST: the pure-Python redaction layer.

## Candidate surface

Only `workspace/redaction.py` may be edited. It is a copy of
`praxist/core/redaction.py` from the pristine PRAXIST source.

Do not overwrite the seed file in place: the task guard treats it as protected.
Create a candidate directory under `experiments/.../variants/<peer_id>_<name>/`
containing `redaction.py`, and score it with:

```bash
python evaluations/run.py --workspace experiments/run_redaction_direct_1/variants/<peer_id>_<name>
```

Forbidden:

- `evaluations/**`
- `sealed_tests/**`
- `assets/**`
- `task.yaml`
- anything outside this task project

## Contract

The candidate must preserve the exact behavior of:

- `redact_text(text) -> (redacted, hits)`
- `redact_json(value) -> (redacted, hits)`
- `dumps_redacted(value, **kwargs)`
- `scan_text(text) -> hits`

The sealed golden cases cover bearer tokens, OpenAI-style keys, GitHub tokens,
named secrets, nested JSON, unicode, empty input, clean text, and near-miss
strings. All cases must match exactly.

## Score

```text
deterministic_score = correctness_rate * (baseline_median_ms / candidate_median_ms)
```

The baseline is the pristine module. A correct baseline-equal implementation
scores `1.0`. A correct faster implementation scores above `1.0`. Any
correctness failure rejects the candidate regardless of speed.

The benchmark is a deterministic mixed corpus: about 90% benign lines and 10%
secret-bearing lines. It is intentionally a throughput task, not a request to
weaken the redaction rules.

## Why this task

This is a narrow but real self-improvement loop on PRAXIST's own code:

- the candidate is a PRAXIST subsystem, not a toy function;
- the evaluator and golden cases are outside the candidate's writable surface;
- the metric rewards a capability improvement that can compound across
  generations;
- every generation is retained as evidence with a score, tests, and a diff.

It is **not** full PRAXIST RSI. It is one subsystem with a sealed evaluator and
a measurable score curve. Full-system RSI still needs a kernel/candidate split,
cross-generation promotion gates, and a broader capability benchmark.
