"""Collect generation winners from a PRAXIST frontier into RSI proposals.

This is a read-only adapter. It does not run candidates or approve them. It
turns PRAXIST's promoted frontier entries into append-only promotion proposals
so the RSI score curve and human gate have one canonical source.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def variant_dir(run_dir: Path, variant_id: str) -> Path:
    parts = [p for p in variant_id.split("/") if p]
    if len(parts) >= 2 and parts[0].startswith("gen_"):
        parts = parts[1:]
    name = "_".join(parts)
    return run_dir / "variants" / name


def candidate_file(run_dir: Path, variant_id: str, filename: str) -> Path:
    directory = variant_dir(run_dir, variant_id)
    direct = directory / filename
    if direct.is_file():
        return direct
    # Some tasks keep the candidate directly under variants/<name>.py.
    flat = run_dir / "variants" / (directory.name + ".py")
    if flat.is_file():
        return flat
    return direct


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--filename", default="redaction.py")
    parser.add_argument("--promotions", required=True)
    parser.add_argument("--promote-script", default=str(Path(__file__).with_name("promote.py")))
    parser.add_argument("--record", action="store_true", help="append proposed records")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    manifest_path = run_dir / "frontier" / "frontier_manifest.json"
    if not manifest_path.is_file():
        print(f"frontier manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    collected = []
    for gen_key, entries in sorted(manifest.get("generations", {}).items(), key=lambda kv: int(kv[0])):
        if not entries:
            continue
        entry = sorted(entries, key=lambda e: int(e.get("rank", 999)))[0]
        metrics = entry.get("metrics", {})
        variant_id = entry.get("canonical_variant_id") or entry.get("variant_name", "")
        score = metrics.get("deterministic_score", entry.get("canonical_metric_value"))
        correctness = metrics.get("correctness_rate", 0.0)
        candidate = candidate_file(run_dir, variant_id, args.filename)
        record = {
            "generation": int(gen_key),
            "variant_id": variant_id,
            "candidate": str(candidate),
            "candidate_exists": candidate.is_file(),
            "score": score,
            "correctness": correctness,
            "source_result_path": entry.get("source_result_path", ""),
            "frontier_lane": entry.get("frontier_lane", ""),
            "rank": entry.get("rank"),
        }
        collected.append(record)
        if args.record and candidate.is_file() and score is not None and float(correctness) == 1.0:
            cmd = [
                sys.executable, args.promote_script,
                "--candidate", str(candidate),
                "--generation", str(gen_key),
                "--score", str(score),
                "--correctness", str(correctness),
                "--metrics-json", json.dumps(metrics, sort_keys=True),
                "--evaluator", "evaluations/run.py",
                "--promotions", args.promotions,
                "--note", f"collected from {entry.get('source_result_path', '')}",
            ]
            subprocess.run(cmd, check=False)

    print(json.dumps({"run_dir": str(run_dir), "collected": collected, "record": args.record}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
