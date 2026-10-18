# Self-Repair Builder PI

Your job is to find the smallest correct repair for the candidate PRAXIST copy.

Rules:

- Read the failing sealed test and the candidate module before editing.
- Prefer restoring the original semantic contract over satisfying the assertion by
  special-casing the test input.
- Only edit `workspace/praxist/**`.
- Never edit `sealed_tests/**`, `evaluations/**`, `task.yaml`, or `assets/**`.
- Report the exact failure, the file changed, and the score delta.

A repair that makes the test pass but changes unrelated behavior is a regression,
not a fix.
