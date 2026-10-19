#!/usr/bin/env node
/*
 * Independent Node.js operator for the PRAXIST operator contract v0.1.
 *
 * This file deliberately shares no code with the Python adapter. It exists to
 * prove that a different front-end implementation can consume the same task
 * project and run artifacts.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const CONTRACT_VERSION = "0.1";

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function readJson(file, fallback = null) {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (_) {
    return fallback;
  }
}

function emit(obj, code = 0) {
  process.stdout.write(JSON.stringify(obj, null, 2) + "\n");
  process.exit(code);
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const k = a.slice(2);
      const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
      args[k] = v;
    } else {
      args._.push(a);
    }
  }
  return args;
}

function operator(args) {
  return {
    name: args.operator || "node-operator",
    version: args["operator-version"] || "0.1",
  };
}

function validate(args) {
  const root = path.resolve(args._[1] || ".");
  const required = ["task.yaml", "description.md", "prompt_task.jinja2", "workspace", "evaluations/run.py"];
  const checks = {};
  const errors = [];
  const warnings = [];
  for (const rel of required) {
    const ok = fs.existsSync(path.join(root, rel));
    checks[rel] = ok ? "pass" : "missing";
    if (!ok) errors.push(`missing required path: ${rel}`);
  }
  const taskYaml = path.join(root, "task.yaml");
  let text = "";
  if (fs.existsSync(taskYaml)) text = fs.readFileSync(taskYaml, "utf8");
  for (const token of ["/home/", "/tmp/", "C:\\", "AppData"]) {
    if (text.includes(token)) warnings.push(`absolute/local path token in task.yaml: ${token}`);
  }
  checks.paths = warnings.length ? "warn" : "pass";
  const evaluator = path.join(root, "evaluations/run.py");
  checks.evaluator = fs.existsSync(evaluator) ? "pass" : "missing";
  const sealed = path.join(root, "sealed_tests");
  checks.protected_surface = fs.existsSync(sealed) ? "pass" : "absent";
  if (!fs.existsSync(sealed)) warnings.push("sealed_tests/ absent; normal task can still run, RSI task must add it");

  emit({
    contract_version: CONTRACT_VERSION,
    ok: errors.length === 0,
    task_project: root,
    task_id: path.basename(root),
    operator: operator(args),
    checks,
    errors,
    warnings,
    hashes: {
      task_yaml: fs.existsSync(taskYaml) ? sha256(taskYaml) : "",
      evaluator: fs.existsSync(evaluator) ? sha256(evaluator) : "",
    },
  }, errors.length ? 2 : 0);
}

function findRunDir(runId, taskProject) {
  const direct = path.resolve(runId);
  if (fs.existsSync(direct) && fs.statSync(direct).isDirectory()) return direct;
  const roots = [];
  if (taskProject) roots.push(path.join(path.resolve(taskProject), "experiments"));
  roots.push(path.join(process.cwd(), "experiments"));
  for (const root of roots) {
    if (!fs.existsSync(root)) continue;
    for (const name of fs.readdirSync(root)) {
      const p = path.join(root, name);
      if (fs.statSync(p).isDirectory() && (name === runId || name.endsWith(runId))) return p;
    }
  }
  throw new Error(`run not found: ${runId}`);
}

function status(args) {
  const runDir = findRunDir(args._[1], args["task-project"]);
  const summary = readJson(path.join(runDir, "run_summary.json"), {}) || {};
  const st = readJson(path.join(runDir, "orchestrator_status.json"), {}) || {};
  const frontier = readJson(path.join(runDir, "frontier", "frontier_manifest.json"), {}) || {};
  let best = null;
  const generations = frontier.generations || {};
  for (const entries of Object.values(generations)) {
    for (const e of entries) {
      if (e.canonical_metric_value == null) continue;
      if (best === null || Number(e.canonical_metric_value) > Number(best.canonical_metric_value)) best = e;
    }
  }
  const state = summary.exit_condition
    ? (summary.exit_code === 0 ? "succeeded" : "failed")
    : (Object.keys(st).length ? "running" : "pending");
  emit({
    contract_version: CONTRACT_VERSION,
    run_id: summary.run_id || path.basename(runDir),
    task_id: best && best.task_id ? best.task_id : path.basename(path.dirname(path.dirname(runDir))),
    state,
    generation: summary.generations_completed != null ? summary.generations_completed : (st.current_generation || 0),
    generations_total: summary.max_generations != null ? summary.max_generations : 4,
    peers: null,
    operator: operator(args),
    provider: summary.credential_failover ? summary.credential_failover.mode : null,
    model: null,
    started_at: null,
    updated_at: new Date(fs.statSync(runDir).mtimeMs).toISOString(),
    exit_condition: summary.exit_condition || null,
    best_metric: best ? {
      name: "canonical_metric_value",
      value: Number(best.canonical_metric_value),
      path: best.source_result_path,
    } : null,
    artifacts: {
      run_dir: runDir,
      run_summary: fs.existsSync(path.join(runDir, "run_summary.json")) ? path.join(runDir, "run_summary.json") : "",
      frontier_manifest: fs.existsSync(path.join(runDir, "frontier", "frontier_manifest.json")) ? path.join(runDir, "frontier", "frontier_manifest.json") : "",
    },
    violations: [],
  });
}

function copyIfExists(src, dst) {
  if (fs.existsSync(src)) {
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(src, dst);
    return true;
  }
  return false;
}

function walk(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const s = fs.statSync(p);
    if (s.isDirectory()) out.push(...walk(p));
    else if (s.isFile()) out.push(p);
  }
  return out;
}

function collect(args) {
  const runDir = findRunDir(args._[1], args["task-project"]);
  const out = path.resolve(args.out);
  fs.mkdirSync(out, { recursive: true });

  copyIfExists(path.join(runDir, "run_summary.json"), path.join(out, "run_summary.json"));
  copyIfExists(path.join(runDir, "orchestrator_status.json"), path.join(out, "orchestrator_status.json"));
  copyIfExists(path.join(runDir, "frontier", "frontier_manifest.json"), path.join(out, "frontier_manifest.json"));

  const results = path.join(runDir, "results");
  for (const p of walk(results)) {
    if (path.basename(p) !== "evaluation_summary.json") continue;
    const rel = path.relative(results, p);
    const dst = path.join(out, "evaluations", rel);
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(p, dst);
  }

  const sessions = path.join(runDir, "gen_0");
  if (fs.existsSync(sessions)) {
    fs.cpSync(sessions, path.join(out, "sessions"), { recursive: true });
  }

  const artifacts = walk(out).map((p) => ({
    path: path.relative(out, p).split(path.sep).join("/"),
    sha256: sha256(p),
  })).sort((a, b) => a.path.localeCompare(b.path));

  const manifest = {
    contract_version: CONTRACT_VERSION,
    run_id: path.basename(runDir),
    task_id: args["task-id"] || path.basename(path.dirname(path.dirname(runDir))),
    engine_commit: args["engine-commit"] || "",
    operator: operator(args),
    provider: args.provider || "",
    model: args.model || "",
    hashes: {
      task_yaml: args["task-yaml-hash"] || "",
      evaluator: args["evaluator-hash"] || "",
      sealed_manifest: args["sealed-manifest-hash"] || "",
    },
    artifacts,
  };
  fs.writeFileSync(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  emit({ ok: true, manifest: path.join(out, "manifest.json"), artifacts: artifacts.length });
}

function runTask(args) {
  const task = path.resolve(args._[1] || ".");
  const cfg = JSON.parse(fs.readFileSync(path.resolve(args.config), "utf8"));
  const env = { ...process.env };
  if (cfg.env_file && fs.existsSync(cfg.env_file)) {
    for (const raw of fs.readFileSync(cfg.env_file, "utf8").split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith("#") || !line.includes("=")) continue;
      const idx = line.indexOf("=");
      env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim().replace(/^["']|["']$/g, "");
    }
  }
  const cmd = [
    cfg.python || "python3", "-m", "praxist.run", "run",
    "--task-path", task,
    "--workspace", cfg.workspace || task,
    "--run-dir", cfg.run_dir,
    "--runtime", cfg.runtime || "agent_runtime:claude_sdk",
    "--model-provider", cfg.model_provider,
    "--model", cfg.model,
  ];
  if (cfg.local !== false) cmd.push("--local");
  if (Array.isArray(cfg.extra_args)) cmd.push(...cfg.extra_args);
  const { spawnSync } = require("child_process");
  const proc = spawnSync(cmd[0], cmd.slice(1), { cwd: task, env, stdio: "inherit" });
  process.exit(proc.status === null ? 1 : proc.status);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const cmd = args._[0];
  if (cmd === "validate") validate(args);
  else if (cmd === "status") status(args);
  else if (cmd === "collect") collect(args);
  else if (cmd === "run") runTask(args);
  else emit({ ok: false, error: "usage: node_operator.js validate|run|status|collect ..." }, 2);
}

main();
