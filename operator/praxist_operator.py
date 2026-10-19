#!/usr/bin/env python3
"""Portable PRAXIST operator adapter (contract v0.1).

This is deliberately independent of Hermes and of any agent SDK. Any front-end
can call these subcommands; the engine remains the separate `praxist` runtime.

Commands:
  validate  check a task project and its protected surface
  run       launch praxist.run with an explicit config
  status    read run status and best frontier metric
  collect   copy run evidence into a standard evidence directory
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CONTRACT_VERSION = "0.1"
OPERATOR_NAME = "portable-operator"
OPERATOR_VERSION = "0.1"

REQUIRED = ("task.yaml", "description.md", "prompt_task.jinja2", "workspace", "evaluations/run.py")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_out(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def cmd_validate(args) -> int:
    root = Path(args.task_project).resolve()
    checks = {}
    errors = []
    warnings = []

    for rel in REQUIRED:
        p = root / rel
        ok = p.exists()
        checks[rel] = "pass" if ok else "missing"
        if not ok:
            errors.append(f"missing required path: {rel}")

    task_yaml = root / "task.yaml"
    text = task_yaml.read_text(encoding="utf-8") if task_yaml.exists() else ""
    for token in ("/home/", "/tmp/", "C:\\", "AppData"):
        if token in text:
            warnings.append(f"absolute/local path token in task.yaml: {token}")
    checks["paths"] = "warn" if warnings else "pass"

    evaluator = root / "evaluations" / "run.py"
    checks["evaluator"] = "pass" if evaluator.is_file() else "missing"
    if not evaluator.is_file():
        errors.append("evaluations/run.py missing")

    protected = root / "sealed_tests"
    if protected.exists():
        checks["protected_surface"] = "pass"
    else:
        checks["protected_surface"] = "absent"
        warnings.append("sealed_tests/ absent; normal task can still run, RSI task must add it")

    result = {
        "contract_version": CONTRACT_VERSION,
        "ok": not errors,
        "task_project": str(root),
        "task_id": root.name,
        "operator": {"name": args.operator, "version": args.operator_version},
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "hashes": {
            "task_yaml": sha256(task_yaml) if task_yaml.exists() else "",
            "evaluator": sha256(evaluator) if evaluator.exists() else "",
        },
    }
    return json_out(result, 0 if result["ok"] else 2)


def find_run_dir(run_id: str, task_project: str | None) -> Path:
    direct = Path(run_id)
    if direct.is_dir():
        return direct.resolve()
    roots = []
    if task_project:
        roots.append(Path(task_project).resolve() / "experiments")
    roots.append(Path.cwd() / "experiments")
    for root in roots:
        if root.is_dir():
            for p in root.iterdir():
                if p.is_dir() and (p.name == run_id or p.name.endswith(run_id)):
                    return p.resolve()
    raise SystemExit(f"run not found: {run_id}")


def read_json(path: Path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def cmd_status(args) -> int:
    run_dir = find_run_dir(args.run_id, args.task_project)
    summary = read_json(run_dir / "run_summary.json", {}) or {}
    status = read_json(run_dir / "orchestrator_status.json", {}) or {}
    frontier = read_json(run_dir / "frontier" / "frontier_manifest.json", {}) or {}

    best = None
    best_value = None
    best_path = None
    for entries in (frontier.get("generations") or {}).values():
        for e in entries:
            v = e.get("canonical_metric_value")
            if v is None:
                continue
            if best_value is None or float(v) > float(best_value):
                best_value = float(v)
                best = e
                best_path = e.get("source_result_path")

    state = status.get("current_generation") is not None and status.get("generations_completed", 0) == 0
    if summary.get("exit_condition"):
        state_name = "succeeded" if summary.get("exit_code") == 0 else "failed"
    elif status:
        state_name = "running"
    else:
        state_name = "pending"

    payload = {
        "contract_version": CONTRACT_VERSION,
        "run_id": summary.get("run_id") or run_dir.name,
        "task_id": (best or {}).get("task_id") or run_dir.parent.parent.name,
        "state": state_name,
        "generation": summary.get("generations_completed", status.get("current_generation", 0)),
        "generations_total": summary.get("max_generations", 4),
        "peers": None,
        "operator": {"name": args.operator, "version": args.operator_version},
        "provider": (summary.get("credential_failover") or {}).get("mode"),
        "model": None,
        "started_at": None,
        "updated_at": datetime.fromtimestamp(run_dir.stat().st_mtime, timezone.utc).isoformat(),
        "exit_condition": summary.get("exit_condition"),
        "best_metric": {
            "name": "canonical_metric_value",
            "value": best_value,
            "path": best_path,
        } if best_value is not None else None,
        "artifacts": {
            "run_dir": str(run_dir),
            "run_summary": str(run_dir / "run_summary.json") if (run_dir / "run_summary.json").exists() else "",
            "frontier_manifest": str(run_dir / "frontier" / "frontier_manifest.json") if (run_dir / "frontier" / "frontier_manifest.json").exists() else "",
        },
        "violations": [],
    }
    return json_out(payload, 0)


def cmd_collect(args) -> int:
    run_dir = find_run_dir(args.run_id, args.task_project)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    copied = []
    for rel in ("run_summary.json", "orchestrator_status.json", "frontier/frontier_manifest.json"):
        src = run_dir / rel
        if src.exists():
            dst = out / Path(rel).name if "/" not in rel else out / "frontier_manifest.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)

    results = run_dir / "results"
    if results.is_dir():
        evals = out / "evaluations"
        evals.mkdir(exist_ok=True)
        for summary in results.glob("**/evaluation_summary.json"):
            rel = summary.relative_to(results)
            dst = evals / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(summary, dst)
            copied.append(dst)

    sessions = run_dir / "gen_0"
    if sessions.is_dir():
        dst = out / "sessions"
        shutil.copytree(sessions, dst, dirs_exist_ok=True)
        copied.append(dst)

    artifacts = []
    for p in sorted(out.rglob("*")):
        if p.is_file():
            artifacts.append({"path": str(p.relative_to(out)), "sha256": sha256(p)})

    manifest = {
        "contract_version": CONTRACT_VERSION,
        "run_id": run_dir.name,
        "task_id": args.task_id or run_dir.parent.parent.name,
        "engine_commit": args.engine_commit or "",
        "operator": {"name": args.operator, "version": args.operator_version},
        "provider": args.provider or "",
        "model": args.model or "",
        "hashes": {
            "task_yaml": args.task_yaml_hash or "",
            "evaluator": args.evaluator_hash or "",
            "sealed_manifest": args.sealed_manifest_hash or "",
        },
        "artifacts": artifacts,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return json_out({"ok": True, "manifest": str(out / "manifest.json"), "artifacts": len(artifacts)})


def cmd_run(args) -> int:
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    env = os.environ.copy()
    env_file = cfg.get("env_file")
    if env_file and Path(env_file).is_file():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    cmd = [
        cfg.get("python", sys.executable), "-m", "praxist.run", "run",
        "--task-path", str(Path(args.task_project).resolve()),
        "--workspace", cfg.get("workspace", str(Path(args.task_project).resolve() / "workspace")),
        "--run-dir", cfg["run_dir"],
        "--runtime", cfg.get("runtime", "agent_runtime:claude_sdk"),
        "--model-provider", cfg["model_provider"],
        "--model", cfg["model"],
    ]
    if cfg.get("local", True):
        cmd.append("--local")
    cmd.extend(cfg.get("extra_args", []))
    proc = subprocess.run(cmd, cwd=str(Path(args.task_project).resolve()), env=env)
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--operator", default=OPERATOR_NAME)
    ap.add_argument("--operator-version", default=OPERATOR_VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("task_project")
    v.set_defaults(func=cmd_validate)

    s = sub.add_parser("status")
    s.add_argument("run_id")
    s.add_argument("--task-project", default="")
    s.set_defaults(func=cmd_status)

    c = sub.add_parser("collect")
    c.add_argument("run_id")
    c.add_argument("--task-project", default="")
    c.add_argument("--out", required=True)
    c.add_argument("--task-id", default="")
    c.add_argument("--engine-commit", default="")
    c.add_argument("--provider", default="")
    c.add_argument("--model", default="")
    c.add_argument("--task-yaml-hash", default="")
    c.add_argument("--evaluator-hash", default="")
    c.add_argument("--sealed-manifest-hash", default="")
    c.set_defaults(func=cmd_collect)

    r = sub.add_parser("run")
    r.add_argument("task_project")
    r.add_argument("--config", required=True)
    r.set_defaults(func=cmd_run)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
