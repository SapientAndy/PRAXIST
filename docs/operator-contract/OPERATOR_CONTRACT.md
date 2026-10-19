# PRAXIST Operator Contract v0.1

**目的：让任何前端 Agent 都能用同一套输入、状态和证据格式驱动 PRAXIST，而不依赖 Hermes 的会话记忆或私有脚本。**

这不是法律合同，也不是某个 Skill。它是 Operator（前端 Agent）与 PRAXIST Engine 之间的接口规范。

---

## 1. 角色

| 角色 | 负责 |
|---|---|
| **Human** | 目标、评估器、baseline、晋升决定 |
| **Operator** | intake、task project、validate、launch、monitor、collect、evidence |
| **PRAXIST Engine** | peers、generations、frontier、panel、run artifacts、resume/replay |

Operator 不拥有 Engine，也不修改 Engine 的评估器。Engine 不依赖某个 Operator 的私有状态。

---

## 2. 生命周期

```text
intake
  → task-project
  → validate
  → canary
  → launch
  → monitor
  → collect
  → human decision
  → promote / reject / hold
```

### 2.1 intake

Operator 把 Idea 转成 task project：

```text
task-project/
  task.yaml
  description.md
  prompt_task.jinja2
  roles/
  workspace/
  evaluations/run.py
  assets/baseline.json
  sealed_tests/          # optional but required for RSI tasks
```

要求：

- 不写绝对路径；
- 不把 evaluator 放进 candidate workspace；
- baseline 必须来自实际测量，不是猜测；
- task.yaml 里声明 writable/protected roots。

### 2.2 validate

Operator 运行：

```bash
praxist validate <task-project> --json
```

必须返回：

```json
{
  "ok": true,
  "task_id": "...",
  "engine_commit": "...",
  "checks": {
    "task_spec": "pass",
    "evaluator": "pass",
    "baseline": "pass",
    "paths": "pass",
    "protected_surface": "pass"
  }
}
```

失败时 `ok=false`，并给出可操作的错误，不得启动 run。

### 2.3 canary

对重型任务，先跑 one-unit / one-generation canary。Canary 通过后才能 launch。

### 2.4 launch

Operator 启动 run，并拿到稳定 `run_id`：

```bash
praxist run <task-project> --config <operator-config.json> --json
```

返回：

```json
{
  "run_id": "run_...",
  "run_dir": "/.../experiments/run_...",
  "state": "running"
}
```

要求：

- `run_id` 幂等、可恢复；
- provider/model 来自 config，不来自 Operator 的名字；
- 不把 API key 写进 run metadata 或日志。

### 2.5 monitor

```bash
praxist status <run-id> --json
```

返回 `status.schema.json` 兼容对象，至少包含：

- `state`: `pending|running|closing|succeeded|failed|cancelled`
- `generation` / `generations_total`
- `peers`
- `best_metric`（name/value/path）
- `artifacts`
- `violations`

### 2.6 collect

```bash
praxist collect <run-id> --out <evidence-dir> --json
```

必须产出：

```text
evidence/
  manifest.json
  run_summary.json
  frontier_manifest.json
  evaluations/
    <peer>/<candidate>/evaluation_summary.json
  sessions/
  checksums.sha256
```

`manifest.json` 至少包含：

- contract version
- run_id / task_id
- engine commit
- operator name/version
- provider/model
- task.yaml / evaluator / sealed manifest 的 sha256
- artifact 列表与 sha256

### 2.7 human decision

Promotion 只能由人记录：

```text
decision: promote | reject | hold
approver: <name>
approved_at: <ISO-8601>
notes: ...
```

Operator 可以准备审批包，但不能自动 `promote`。

---

## 3. 责任边界

### Operator 必须做

- 生成完整 task project；
- 运行 validate / canary；
- 记录 operator 名称、版本、provider、model；
- 收集完整证据；
- 把晋升决定交给人。

### Operator 不能做

- 修改 evaluator、sealed tests、baseline；
- 跳过 validate / canary；
- 自动批准 promotion；
- 把候选写在 evaluator 可写目录；
- 把 API key 写入日志、metadata、prompt。

### Engine 必须做

- 维护 run dir、frontier、generation boundary；
- 提供 resume/replay；
- 保证 candidate 不能写 evaluator/kernel；
- 输出稳定 artifact。

---

## 4. “无损”的定义

不是“不同 Agent 输出完全一样”，而是：

1. **功能无损**：任何实现本 contract 的 Operator 都能完成同一生命周期；
2. **证据无损**：所有决策和评估都在标准 artifact 里，不依赖会话记忆；
3. **复现无损**：同一 task project、engine commit、provider/model、seeds → 同一评估语义和证据结构。

不同 Operator 可以使用不同 UI、不同模型、不同并发策略；这些必须记录在 metadata 里，不能隐藏。

---

## 5. 一致性等级

| 等级 | 要求 |
|---|---|
| C0 | 能生成合法 task project |
| C1 | 能 validate + collect 已有 run |
| C2 | 能 launch 1 peer / 1 generation smoke |
| C3 | 两个 Operator 对同一 task 产出同结构证据 |
| C4 | RSI task boundary 通过（evaluator 在 candidate 外、promotion 只追加） |

当前目标：先做到 **C3**，再做 RSI 的 C4。

---

## 6. 与 Skill 的关系

- `praxist-takeover` / `praxist-task-initialization` 是某个 Agent 的 Skill，属于 Operator 实现；
- Operator contract 是实现无关的规范；
- 一个 Skill 可以实现 contract，但不能替代 contract。

---

## 7. 最小命令集

```bash
praxist validate <task-project> --json
praxist run <task-project> --config <config> --json
praxist status <run-id> --json
praxist collect <run-id> --out <dir> --json
praxist promote <run-id> --decision <promote|reject|hold> --approver <name> --json
```

其中 `promote` 必须要求人类提供 approver，不能由 Operator 自动调用。
