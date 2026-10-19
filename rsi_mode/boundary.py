#!/usr/bin/env python3
"""Check the RSI boundary for a task project.

The point is not to score a candidate. It is to refuse to call a task "RSI" if
the candidate can edit its own evaluator, baseline, or sealed tests.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-project", required=True)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    root = Path(args.task_project).resolve()
    workspace = root / "workspace"
    evaluator = root / "evaluations" / "run.py"
    sealed = root / "sealed_tests"
    baseline = root / "assets" / "baseline.json"
    promotions = root / "promotions" / "promotions.jsonl"
    task_yaml = root / "task.yaml"

    checks = []
    errors = []
    warnings = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            errors.append(f"{name}: {detail}")

    add("workspace_exists", workspace.is_dir(), "candidate root")
    add("evaluator_outside_candidate", evaluator.is_file() and workspace not in evaluator.parents, str(evaluator))
    add("sealed_tests_outside_candidate", sealed.is_dir() and workspace not in sealed.parents, str(sealed))
    add("baseline_exists", baseline.is_file(), str(baseline))
    add("promotions_append_log", promotions.is_file(), str(promotions))

    if task_yaml.is_file():
        text = task_yaml.read_text(encoding="utf-8")
        add("task_declares_sealed_tests", "sealed_tests" in text, "task.yaml mentions sealed_tests")
        add("task_declares_evaluator", "evaluations" in text, "task.yaml mentions evaluations")
        add("task_declares_baseline", "baseline" in text, "task.yaml mentions baseline")
        if "/home/" in text or "/tmp/" in text or "C:\\" in text:
            warnings.append("task.yaml contains absolute/local paths")
    else:
        add("task_yaml_exists", False, "missing task.yaml")

    if promotions.is_file():
        statuses = []
        for line in promotions.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                statuses.append(json.loads(line).get("status"))
            except Exception:
                errors.append("promotions.jsonl has invalid JSON line")
        add("promotion_statuses_valid", all(s in ("proposed", "approved") for s in statuses), str(statuses))
    else:
        add("promotion_statuses_valid", False, "no promotion log")

    for forbidden in ("evaluations", "sealed_tests", "assets"):
        p = workspace / forbidden
        add(f"candidate_does_not_own_{forbidden}", not p.exists(), str(p))

    result = {
        "contract_version": "0.1",
        "task_project": str(root),
        "ok": not errors,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "rsi_ready": not errors and sealed.is_dir() and evaluator.is_file() and promotions.is_file(),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
