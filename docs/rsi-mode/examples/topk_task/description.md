# Top-K Algorithm Optimization

This is a small but real code-optimization task. It is intentionally cheap to
evaluate on a CPU, but it has a correctness contract, a measurable speed metric,
and a non-trivial algorithm-design surface.

## Candidate

Edit only:

```text
workspace/solution.py
```

The file must define:

```python
def top_k(items, k):
    ...
```

Contract:

- return the `k` largest items in descending order;
- return `[]` when `k <= 0`;
- preserve duplicates;
- accept any iterable of integers.

## Baseline

`assets/baseline/solution.py` is the frozen reference implementation. It is
correct but uses a full sort.

## Evaluation

`evaluations/run.py` copies `workspace/` to a temporary directory, imports the
candidate, runs correctness cases, and benchmarks it against the baseline on a
fixed 200,000-integer workload with `k=10`.

Primary metric:

```text
deterministic_score = correctness_rate * (baseline_median_ms / candidate_median_ms)
```

- A baseline-equal implementation scores `1.0`.
- A faster correct implementation scores above `1.0`.
- An incorrect implementation scores `0.0`, regardless of speed.

Run the evaluator locally:

```bash
python evaluations/run.py --output-dir experiments/manual
```

Do not edit `evaluations/`, `assets/`, `task.yaml`, or any file outside
`workspace/solution.py`.
