# PRAXIST Redaction Throughput v2 (safe parent)

This is a PRAXIST self-improvement task for one security-critical subsystem of
PRAXIST: the pure-Python redaction layer. The starting workspace is the safe
`span_slice` parent that passed the hardened 29-case evaluator and the 1,200-case
differential fuzz; the task is to improve it without regressing exactness.

## Candidate surface

Only `workspace/redaction.py` may be edited. It is the safe `span_slice` parent;
the pristine module remains the frozen baseline reference.

Do not overwrite the seed file in place: the task guard treats it as protected.
Create a candidate directory under `experiments/.../variants/<peer_id>_<name>/`
containing `redaction.py`, and score it with:

```bash
python evaluations/run.py --workspace experiments/run_redaction_speed_v2/variants/<peer_id>_<name>
```

## Contract

The candidate must preserve the exact behavior of:

- `redact_text(text) -> (redacted, hits)`
- `redact_json(value) -> (redacted, hits)`
- `dumps_redacted(value, **kwargs)`
- `scan_text(text) -> hits`

The sealed golden cases cover bearer tokens, OpenAI-style keys, GitHub tokens,
named secrets, nested JSON, unicode, empty input, clean text, near-miss strings,
cross-line secrets, duplicate secrets, and Unicode length changes. All 29 cases
must match exactly.

## Score

```text
deterministic_score = correctness_rate * (baseline_median_ms / candidate_median_ms)
```

The baseline is the safe `span_slice` parent, so a parent-equal implementation
scores `1.0`. A correct faster implementation scores above `1.0`. Any
correctness failure rejects the candidate regardless of speed.

The benchmark is a deterministic mixed corpus of 945,159 characters, about 90%
benign lines and 10% secret-bearing lines. It is intentionally a throughput task,
not a request to weaken the redaction rules.

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
