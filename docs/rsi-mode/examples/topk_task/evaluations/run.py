#!/usr/bin/env python3
"""Public evaluator for the top-k optimization task.

The evaluator copies the candidate workspace to a temporary directory, imports
``solution.py`` from that copy, runs correctness tests, and benchmarks it against
the read-only baseline. The candidate cannot edit this file or the baseline.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import statistics
import sys
import tempfile
import time
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = TASK_ROOT / "assets" / "baseline" / "solution.py"
DEFAULT_WORKSPACE = TASK_ROOT / "workspace"


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_top_k(values: list[int], k: int) -> list[int]:
    if k <= 0:
        return []
    return sorted(values, reverse=True)[:k]


def benchmark_pair(base_fn: Any, candidate_fn: Any, values: list[int], k: int, repeats: int = 9) -> tuple[float, float, float]:
    """Benchmark baseline and candidate alternately to reduce CPU drift."""
    base_fn(values, k)
    candidate_fn(values, k)
    base_times: list[float] = []
    candidate_times: list[float] = []
    ratios: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        base_fn(values, k)
        base_ms = (time.perf_counter() - start) * 1000.0

        start = time.perf_counter()
        candidate_fn(values, k)
        candidate_ms = (time.perf_counter() - start) * 1000.0

        base_times.append(base_ms)
        candidate_times.append(candidate_ms)
        if candidate_ms > 0:
            ratios.append(base_ms / candidate_ms)
    return statistics.median(base_times), statistics.median(candidate_times), statistics.median(ratios)


def evaluate(workspace: Path) -> dict[str, Any]:
    baseline = load_module(BASELINE_FILE, "topk_baseline")
    candidate_file = workspace / "solution.py"
    if not candidate_file.is_file():
        raise FileNotFoundError(f"candidate solution not found: {candidate_file}")
    candidate = load_module(candidate_file, "topk_candidate")

    test_cases: list[tuple[list[int], int]] = [
        ([], 3),
        ([3, 1, 2], 2),
        ([5, 5, 5, 1], 3),
        (list(range(1000)), 10),
        ([9, -1, 0, 4, 4, 2], 6),
        ([1, 2, 3], 0),
        ([1, 2, 3], 5),
    ]
    failures: list[str] = []
    for index, (values, k) in enumerate(test_cases):
        expected = expected_top_k(values, k)
        try:
            actual = candidate.top_k(values, k)
        except Exception as exc:  # noqa: BLE001 - report candidate failures
            failures.append(f"case {index} raised {type(exc).__name__}: {exc}")
            continue
        if actual != expected:
            failures.append(f"case {index}: expected {expected!r}, got {actual!r}")

    rng = random.Random(123456)
    values = [rng.randint(-10**9, 10**9) for _ in range(200_000)]
    k = 10
    baseline_ms, candidate_ms, speedup = benchmark_pair(
        baseline.top_k, candidate.top_k, values, k
    )
    if abs(speedup - 1.0) <= 0.05:
        speedup = 1.0

    total = len(test_cases)
    passed = total - len(failures)
    correctness_rate = passed / total
    score = correctness_rate * speedup if correctness_rate == 1.0 else 0.0

    metrics: dict[str, Any] = {
        "deterministic_score": round(score, 6),
        "correctness_rate": round(correctness_rate, 6),
        "speedup": round(speedup, 6),
        "candidate_median_ms": round(candidate_ms, 6),
        "baseline_median_ms": round(baseline_ms, 6),
        "scored_complete": True,
        "protocol_integrity_passed": True,
        "promotion_eligible": correctness_rate == 1.0,
        "confirmed_performance_gate_passed": correctness_rate == 1.0 and speedup > 1.0,
        "is_smoke_eval": False,
        "partial": False,
        "scout_only": False,
        "validation_only": False,
        "late_after_generation_boundary": False,
        "suspect_protocol": False,
        "suspect_leakage": False,
    }
    return {
        "task_id": "topk_optimization",
        "primary_metric": "deterministic_score",
        "direction": "maximize",
        "metrics": metrics,
        "passed": passed,
        "failed": len(failures),
        "total": total,
        "complete": True,
        "ok": correctness_rate == 1.0,
        "evidence_stage": "complete",
        "evidence_source": "evaluations/run.py",
        "evaluator": "evaluations/run.py",
        "failures": failures,
        "candidate": str(candidate_file),
    }


def failure_summary(error: str) -> dict[str, Any]:
    return {
        "task_id": "topk_optimization",
        "primary_metric": "deterministic_score",
        "direction": "maximize",
        "metrics": {
            "deterministic_score": 0.0,
            "correctness_rate": 0.0,
            "speedup": 0.0,
            "candidate_median_ms": 0.0,
            "baseline_median_ms": 0.0,
            "scored_complete": False,
            "protocol_integrity_passed": False,
            "promotion_eligible": False,
            "confirmed_performance_gate_passed": False,
            "is_smoke_eval": True,
            "partial": False,
            "scout_only": False,
            "validation_only": False,
            "late_after_generation_boundary": False,
            "suspect_protocol": True,
            "suspect_leakage": False,
        },
        "passed": 0,
        "failed": 1,
        "total": 1,
        "complete": False,
        "ok": False,
        "evidence_stage": "preliminary",
        "evidence_source": "evaluations/run.py",
        "evaluator": "evaluations/run.py",
        "failures": [error],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="topk-candidate-") as tmp:
            candidate = Path(tmp) / "workspace"
            candidate.mkdir(parents=True, exist_ok=True)
            for source in args.workspace.rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    target = candidate / source.relative_to(args.workspace)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
            summary = evaluate(candidate)
    except Exception as exc:  # noqa: BLE001 - evaluator must emit a summary
        summary = failure_summary(f"{type(exc).__name__}: {exc}")
        (args.output_dir / "failure_traceback.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )

    summary_path = args.output_dir / "evaluation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
