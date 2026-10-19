#!/usr/bin/env python3
"""C1 conformance check for the PRAXIST operator contract.

Runs the portable operator twice, with two different operator names, against the
same task project and run directory. It verifies that the task hashes, status
shape, and evidence manifest structure are identical; only operator metadata
may differ.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADAPTER = HERE / "praxist_operator.py"


def call(args: list[str]) -> dict:
    proc = subprocess.run([sys.executable, str(ADAPTER), *args], capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {"ok": False, "raw_stdout": proc.stdout, "raw_stderr": proc.stderr, "returncode": proc.returncode}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-project", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    task = str(Path(args.task_project).resolve())
    checks = []
    val_a = call(["--operator", "conformance-a", "validate", task])
    val_b = call(["--operator", "conformance-b", "validate", task])
    checks.append({
        "name": "validate_same_hashes",
        "ok": val_a.get("hashes") == val_b.get("hashes") and bool(val_a.get("ok")) and bool(val_b.get("ok")),
        "a": val_a.get("hashes"),
        "b": val_b.get("hashes"),
    })

    status_a = call(["--operator", "conformance-a", "status", args.run_id, "--task-project", task])
    status_b = call(["--operator", "conformance-b", "status", args.run_id, "--task-project", task])
    stable_keys = ("contract_version", "run_id", "task_id", "state", "generation", "generations_total", "exit_condition", "best_metric")
    checks.append({
        "name": "status_same_semantics",
        "ok": all(status_a.get(k) == status_b.get(k) for k in stable_keys),
        "a": {k: status_a.get(k) for k in stable_keys},
        "b": {k: status_b.get(k) for k in stable_keys},
    })

    with tempfile.TemporaryDirectory(prefix="praxist_conformance_") as td:
        out_a = Path(td) / "a"
        out_b = Path(td) / "b"
        col_a = call(["--operator", "conformance-a", "collect", args.run_id, "--task-project", task, "--out", str(out_a)])
        col_b = call(["--operator", "conformance-b", "collect", args.run_id, "--task-project", task, "--out", str(out_b)])
        man_a = json.loads((out_a / "manifest.json").read_text()) if (out_a / "manifest.json").exists() else {}
        man_b = json.loads((out_b / "manifest.json").read_text()) if (out_b / "manifest.json").exists() else {}
        # Operator metadata is the only allowed difference.
        allowed_diff = {"operator"}
        keys = sorted(set(man_a) | set(man_b))
        diffs = [k for k in keys if k not in allowed_diff and man_a.get(k) != man_b.get(k)]
        checks.append({
            "name": "evidence_same_hashes",
            "ok": col_a.get("ok") and col_b.get("ok") and not diffs,
            "diffs": diffs,
            "artifacts_a": len(man_a.get("artifacts", [])),
            "artifacts_b": len(man_b.get("artifacts", [])),
        })

    report = {
        "contract_version": "0.1",
        "task_project": task,
        "run_id": args.run_id,
        "checks": checks,
        "ok": all(c["ok"] for c in checks),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
