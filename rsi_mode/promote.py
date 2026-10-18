"""Append-only promotion records for the PRAXIST-RSI prototype.

The evaluator is the only source of a score. This tool never runs a candidate
and never edits the sealed evaluator. It records a proposal, checks monotonicity
against approved records, and leaves the final approval to a human gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--generation", required=True, type=int)
    parser.add_argument("--score", required=True, type=float)
    parser.add_argument("--correctness", required=True, type=float)
    parser.add_argument("--metrics-json", default="{}")
    parser.add_argument("--evaluator", default="evaluations/run.py")
    parser.add_argument("--sealed-manifest", default="")
    parser.add_argument("--promotions", default="promotions/promotions.jsonl")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--approver", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    candidate = Path(args.candidate).resolve()
    if not candidate.is_file():
        print(f"candidate not found: {candidate}", file=sys.stderr)
        return 2
    if args.correctness < 1.0:
        print("refusing to promote: correctness is below 1.0", file=sys.stderr)
        return 2
    if args.score <= 0:
        print("refusing to promote: score must be positive", file=sys.stderr)
        return 2

    promotions = Path(args.promotions).resolve()
    promotions.parent.mkdir(parents=True, exist_ok=True)
    records = read_records(promotions)
    approved = [r for r in records if r.get("status") == "approved"]
    best = max((float(r.get("score", 0)) for r in approved), default=0.0)
    candidate_hash = sha256_file(candidate)
    if any(r.get("candidate_sha256") == candidate_hash for r in records):
        print("refusing to promote: candidate hash already recorded", file=sys.stderr)
        return 2
    if args.approve and args.score <= best:
        print(
            f"refusing to approve: score {args.score} does not exceed best approved {best}",
            file=sys.stderr,
        )
        return 2

    sealed_hash = ""
    if args.sealed_manifest:
        sealed_path = Path(args.sealed_manifest)
        if sealed_path.is_file():
            sealed_hash = sha256_file(sealed_path)

    record = {
        "schema_version": 1,
        "promotion_id": f"gen{args.generation}_{candidate_hash[:12]}",
        "generation": args.generation,
        "candidate_path": str(candidate),
        "candidate_sha256": candidate_hash,
        "candidate_bytes": candidate.stat().st_size,
        "score": args.score,
        "correctness": args.correctness,
        "metrics": json.loads(args.metrics_json),
        "evaluator": args.evaluator,
        "sealed_manifest_sha256": sealed_hash,
        "status": "approved" if args.approve else "proposed",
        "approver": args.approver if args.approve else "",
        "note": args.note,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "previous_best_approved": best,
    }
    with promotions.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    print(json.dumps({
        "status": "ok",
        "record": record,
        "promotions": str(promotions),
        "best_approved_before": best,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
