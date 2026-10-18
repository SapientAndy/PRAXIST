#!/usr/bin/env python3
"""Sealed evaluator for the PRAXIST self-improvement prototype.

The candidate workspace contains a copy of the `praxist` package. The sealed
tests live outside that workspace and are never importable by the candidate at
edit time. This evaluator copies the candidate package to a throwaway directory,
runs the sealed tests against it, and emits a compact JSON metric block.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    total = passed = failed = skipped = 0
    failures = []
    for case in root.iter("testcase"):
        total += 1
        bad = case.find("failure") is not None or case.find("error") is not None
        if bad:
            failed += 1
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            failures.append(name)
        elif case.find("skipped") is not None:
            skipped += 1
        else:
            passed += 1
    scored = max(1, total - skipped)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": round(passed / scored, 6),
        "failures": failures[:20],
    }


# The isolated candidate copy cannot discover the bundled fake runtime plugin.
# It fails identically in the clean baseline and is outside this task's scope.
KNOWN_FAILURE_NAMES = ("test_fake_panel_writes_replayable_run_dir",)


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=str(root / "workspace"))
    ap.add_argument("--tests", default=str(root / "sealed_tests"))
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--json-out", default="")
    ap.add_argument("--output-dir", default="")
    args, _unknown = ap.parse_known_args()

    workspace = Path(args.workspace)
    tests = Path(args.tests)
    package = workspace / "praxist"
    if not package.is_dir():
        raise SystemExit(f"candidate package not found: {package}")
    if not tests.is_dir():
        raise SystemExit(f"sealed tests not found: {tests}")

    with tempfile.TemporaryDirectory(prefix="praxist_sealed_") as td:
        temp = Path(td)
        cand = temp / "cand"
        cand.mkdir()
        shutil.copytree(package, cand / "praxist")

        junit = temp / "junit.xml"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(cand)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        cmd = [
            args.python, "-m", "pytest", str(tests), "-q",
            f"--junitxml={junit}", "-p", "no:cacheprovider",
        ]
        proc = subprocess.run(cmd, cwd=temp, env=env, capture_output=True, text=True)

        if not junit.exists():
            result = {
                "ok": False,
                "error": "pytest did not produce junit.xml",
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-2000:],
            }
        else:
            metrics = parse_junit(junit)
            known = [f for f in metrics["failures"] if any(k in f for k in KNOWN_FAILURE_NAMES)]
            metrics["known_failures"] = known
            metrics["in_scope_failed"] = metrics["failed"] - len(known)
            result = {
                "ok": metrics["in_scope_failed"] == 0,
                "metrics": metrics,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-1000:],
            }

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        metrics = result.get("metrics") or {}
        summary = {
            "task_id": "praxist_self_repair",
            "primary_metric": "pass_rate",
            "direction": "maximize",
            "metrics": metrics,
            "passed": metrics.get("passed"),
            "failed": metrics.get("failed"),
            "total": metrics.get("total"),
            "complete": bool(result.get("ok")),
            "evidence_stage": "complete",
            "evidence_source": "sealed_tests",
            "evaluator": "evaluations/run.py",
            "failures": metrics.get("failures", []),
        }
        (out_dir / "evaluation_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(payload)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
