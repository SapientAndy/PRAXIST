# praxist_redaction_speed

A PRAXIST task that lets the research loop optimize one PRAXIST subsystem
(`praxist/core/redaction.py`) under a sealed correctness and throughput
evaluator.

- Candidate surface: `workspace/redaction.py`
- Sealed checks: `sealed_tests/check.py` + `sealed_tests/golden.json`
- Baseline: `assets/baseline.json`
- Score: `correctness_rate * (baseline_median_ms / candidate_median_ms)`

## Local commands

```bash
python assets/build_golden.py          # regenerate golden cases from baseline
python evaluations/run.py              # score current candidate
praxist resolve .                      # validate task contract
```

## Status

This is a subsystem-level self-improvement task, not full PRAXIST RSI. It
exists to measure whether PRAXIST's research loop can improve a real PRAXIST
module while an external evaluator prevents changes to the rules.
