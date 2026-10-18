from __future__ import annotations

import importlib.util
import json
import os
import random
import statistics
import sys
import time
import traceback
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden.json"


def load_candidate():
    path = Path(os.environ["CANDIDATE_PATH"]).resolve()
    spec = importlib.util.spec_from_file_location("candidate_redaction", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load candidate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stable_hits(hits):
    return sorted(str(x) for x in hits)


def check_case(module, case):
    kind = case["kind"]
    if kind == "text":
        got, hits = module.redact_text(case["input"])
        return got == case["expected"], stable_hits(hits) == stable_hits(case["hits"]), "redact_text"
    if kind == "json":
        got, hits = module.redact_json(case["input"])
        return got == case["expected"], stable_hits(hits) == stable_hits(case["hits"]), "redact_json"
    if kind == "dumps":
        got = module.dumps_redacted(case["input"], sort_keys=True)
        return got == case["expected"], True, "dumps_redacted"
    if kind == "scan":
        got = module.scan_text(case["input"])
        return stable_hits(got) == stable_hits(case["expected"]), True, "scan_text"
    raise ValueError(f"unknown case kind: {kind}")


def build_benchmark_text() -> str:
    rng = random.Random(42)
    words = [
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
        "run", "step", "peer", "panel", "finding", "graph", "memory", "task",
    ]
    lines = []
    for i in range(12000):
        if i % 11 == 0:
            token = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(20))
            lines.append(f"header-{i}: Bearer {token} and sk-{token[:12]}")
        else:
            lines.append(" ".join(rng.choice(words) for _ in range(14)))
    return "\n".join(lines)


def benchmark(module):
    text = build_benchmark_text()
    # Warm up once, then report the median of three independent runs.
    module.redact_text(text)
    samples = []
    for _ in range(3):
        start = time.perf_counter()
        module.redact_text(text)
        samples.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(samples), len(text)


def main() -> int:
    payload = {
        "schema_version": 1,
        "passed": 0,
        "failed": 0,
        "total": 0,
        "correctness_rate": 0.0,
        "candidate_median_ms": None,
        "benchmark_chars": None,
        "failures": [],
    }
    try:
        module = load_candidate()
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        cases = golden["cases"]
        payload["total"] = len(cases)
        for case in cases:
            try:
                output_ok, hits_ok, surface = check_case(module, case)
                if output_ok and hits_ok:
                    payload["passed"] += 1
                else:
                    payload["failed"] += 1
                    payload["failures"].append({
                        "name": case["name"],
                        "surface": surface,
                        "output_ok": output_ok,
                        "hits_ok": hits_ok,
                    })
            except Exception as exc:
                payload["failed"] += 1
                payload["failures"].append({
                    "name": case.get("name", "?"),
                    "exception": type(exc).__name__,
                    "detail": str(exc)[:300],
                })
        if payload["total"]:
            payload["correctness_rate"] = payload["passed"] / payload["total"]
        median_ms, chars = benchmark(module)
        payload["candidate_median_ms"] = round(median_ms, 4)
        payload["benchmark_chars"] = chars
    except Exception as exc:
        payload["failures"].append({
            "name": "__harness__",
            "exception": type(exc).__name__,
            "detail": str(exc)[:500],
            "traceback": traceback.format_exc()[-1500:],
        })
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
