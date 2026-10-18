from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = TASK_ROOT / "workspace"
SEALED_CHECK = TASK_ROOT / "sealed_tests" / "check.py"
BASELINE = TASK_ROOT / "assets" / "baseline.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--output-dir", default=str(TASK_ROOT / "evaluations"))
    parser.add_argument("--json-out", default="")
    args, _unknown = parser.parse_known_args()

    workspace = args.workspace.resolve()
    candidate = workspace / "redaction.py"

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": 1,
        "task_id": "praxist_redaction_speed",
        "primary_metric": "deterministic_score",
        "direction": "maximize",
        "metrics": {},
        "passed": 0,
        "failed": 0,
        "total": 0,
        "complete": False,
        "evidence_stage": "complete",
        "evidence_source": "sealed_tests",
        "evaluator": "evaluations/run.py",
        "failures": [],
    }

    try:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        baseline_ms = float(baseline["baseline_median_ms"])
        if not candidate.is_file():
            raise FileNotFoundError(f"candidate not found: {candidate}")

        with tempfile.TemporaryDirectory(prefix="redaction_candidate_") as tmp:
            candidate_copy = Path(tmp) / "redaction.py"
            shutil.copyfile(candidate, candidate_copy)
            env = dict(os.environ)
            env["CANDIDATE_PATH"] = str(candidate_copy)
            proc = subprocess.run(
                [sys.executable, str(SEALED_CHECK)],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                timeout=120,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"sealed check exited {proc.returncode}: {proc.stderr[-800:]}")
            check = json.loads(proc.stdout.strip().splitlines()[-1])

        correctness = float(check.get("correctness_rate") or 0.0)
        candidate_ms = check.get("candidate_median_ms")
        candidate_ms = float(candidate_ms) if candidate_ms else None
        speedup = baseline_ms / candidate_ms if candidate_ms and candidate_ms > 0 else 0.0
        score = correctness * speedup if candidate_ms else 0.0

        summary["passed"] = int(check.get("passed") or 0)
        summary["failed"] = int(check.get("failed") or 0)
        summary["total"] = int(check.get("total") or 0)
        summary["failures"] = check.get("failures") or []
        summary["metrics"] = {
            "deterministic_score": round(score, 6),
            "correctness_rate": round(correctness, 6),
            "speedup": round(speedup, 6),
            "candidate_median_ms": round(candidate_ms, 4) if candidate_ms else None,
            "baseline_median_ms": round(baseline_ms, 4),
            "benchmark_chars": check.get("benchmark_chars"),
        }
        summary["complete"] = bool(correctness == 1.0 and candidate_ms)
        summary["candidate_sha256"] = sha256(candidate)
        summary["candidate_bytes"] = candidate.stat().st_size
        summary["candidate_path"] = str(candidate)
    except Exception as exc:
        summary["complete"] = False
        summary["failures"].append({
            "name": "__evaluator__",
            "exception": type(exc).__name__,
            "detail": str(exc)[:800],
            "traceback": traceback.format_exc()[-2000:],
        })

    summary_path = output_dir / "evaluation_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ok" if summary["complete"] else "incomplete",
        "summary": str(summary_path),
        "metrics": summary["metrics"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
