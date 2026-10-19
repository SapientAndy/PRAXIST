#!/usr/bin/env python3
"""C3 conformance: Python adapter vs independent Node.js operator."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = HERE / "praxist_operator.py"
NODE = HERE / "node_operator.js"


def run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True)
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

    v_py = run([sys.executable, str(PY), "--operator", "python-operator", "validate", task])
    v_node = run(["node", str(NODE), "--operator", "node-operator", "validate", task])
    checks = [{
        "name": "validate_same_hashes",
        "ok": v_py.get("hashes") == v_node.get("hashes") and bool(v_py.get("ok")) and bool(v_node.get("ok")),
        "python": v_py.get("hashes"),
        "node": v_node.get("hashes"),
    }]

    s_py = run([sys.executable, str(PY), "--operator", "python-operator", "status", args.run_id, "--task-project", task])
    s_node = run(["node", str(NODE), "--operator", "node-operator", "status", args.run_id, "--task-project", task])
    keys = ("contract_version", "run_id", "task_id", "state", "generation", "generations_total", "exit_condition", "best_metric")
    checks.append({
        "name": "status_same_semantics",
        "ok": all(s_py.get(k) == s_node.get(k) for k in keys),
        "python": {k: s_py.get(k) for k in keys},
        "node": {k: s_node.get(k) for k in keys},
    })

    with tempfile.TemporaryDirectory(prefix="praxist_c3_") as td:
        a = Path(td) / "python"
        b = Path(td) / "node"
        run([sys.executable, str(PY), "--operator", "python-operator", "collect", args.run_id,
             "--task-project", task, "--out", str(a), "--task-id", "praxist_bo_c2",
             "--provider", "deepseek", "--model", "deepseek-flash"])
        run(["node", str(NODE), "--operator", "node-operator", "collect", args.run_id,
             "--task-project", task, "--out", str(b), "--task-id", "praxist_bo_c2",
             "--provider", "deepseek", "--model", "deepseek-flash"])
        ma = json.loads((a / "manifest.json").read_text()) if (a / "manifest.json").exists() else {}
        mb = json.loads((b / "manifest.json").read_text()) if (b / "manifest.json").exists() else {}
        allowed = {"operator", "artifacts"}
        diffs = [k for k in sorted(set(ma) | set(mb)) if k not in allowed and ma.get(k) != mb.get(k)]
        aa = sorted([(x["path"], x["sha256"]) for x in ma.get("artifacts", [])])
        bb = sorted([(x["path"], x["sha256"]) for x in mb.get("artifacts", [])])
        if aa != bb:
            diffs.append("artifacts")
        checks.append({
            "name": "evidence_same_hashes",
            "ok": not diffs and len(aa) == len(bb),
            "diffs": diffs,
            "python_artifacts": len(aa),
            "node_artifacts": len(bb),
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
