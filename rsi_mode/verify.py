"""Verify that the sealed surface of a task project did not change.

The candidate may edit only its writable roots. This tool checks the files that
must remain frozen: the evaluator, the sealed checks, the baseline, and the task
contract. It is intentionally independent of the PRAXIST kernel.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-project", required=True)
    parser.add_argument("--manifest", default="assets/protected_manifest.json")
    args = parser.parse_args()

    root = Path(args.task_project).resolve()
    manifest_path = (root / args.manifest).resolve()
    if not manifest_path.is_file():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("files", {})
    ok = True
    results = {}
    for rel, expected in sorted(entries.items()):
        path = (root / rel).resolve()
        if not path.is_file():
            results[rel] = {"status": "missing", "expected": expected}
            ok = False
            continue
        actual = sha256_file(path)
        status = "ok" if actual == expected else "mismatch"
        results[rel] = {"status": status, "expected": expected, "actual": actual}
        if status != "ok":
            ok = False

    print(json.dumps({
        "task_project": str(root),
        "manifest": str(manifest_path),
        "ok": ok,
        "files": results,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
