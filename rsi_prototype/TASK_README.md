# PRAXIST self-repair task

This task measures whether a research loop can repair a candidate copy of
PRAXIST under a sealed test suite.

- Candidate: `workspace/praxist/`
- Scorer: `sealed_tests/` + `evaluations/run.py`
- Clean baseline: 54/55
- Current starting state: 50/55
- Target: 54/55

Only `workspace/praxist/**` may be edited. `sealed_tests/**`,
`evaluations/**`, `task.yaml`, and `assets/**` are out of bounds.

Run `python evaluations/run.py` to see the score and failing test names.

The candidate is a copy of the package. Restore the broken semantic contracts;
do not weaken, skip, or rewrite the sealed tests.
