# Phase 3 — Kernel-copy：候选可以改整个 PRAXIST 包

**结论：peer0 交出了一个通用 prefilter 候选，任务内 4.86×（87.9 ms → 18.1 ms），54/55 测试保持，外部 fuzz 0/1,200；held-out 同形状 4.7–5.0×，长行语料 1.15–1.18×。它比 v6 的 83× 慢，但泛化更好。**

## 任务

- 候选拥有完整 `workspace/praxist/` 包副本，可以改任意模块；
- sealed tests + evaluator 在 workspace 外，不可改；
- 主指标：

```text
deterministic_score =
  in_scope_pass_rate × (baseline_median_ms / candidate_median_ms)
```

## 结果

| 项目 | 基线 | peer0 候选 |
|---|---:|---:|
| 测试 | 54/55 | **54/55** |
| in-scope failures | 0 | **0** |
| benchmark | 87.901 ms | **18.0835 ms** |
| speedup | 1.0 | **4.8608×** |

独立复现（fresh evaluator run）：**18.5207 ms，4.7461×，54/55，in-scope 0**。两次结果一致。

候选只改了 `praxist/core/redaction.py`，但任务边界是完整包副本；其他文件保持不变。

## 外部验证

### 1,200 条差分 fuzz

```text
0 output mismatches / 0 hit mismatches
```

### Held-out、同形状换种子

| 语料 | 加速 | exact |
|---|---:|---|
| seed 43 | 4.707× | ✅ |
| seed 44 | 4.756× | ✅ |
| dense（每 3 行） | 4.970× | ✅ |
| sparse（每 31 行） | 4.970× | ✅ |

### 长行 / 对抗形状

| 语料 | 加速 | exact |
|---|---:|---|
| 长行 sparse | **1.147×** | ✅ |
| 长行 dense | **1.175×** | ✅ |
| 长行 adversarial | **1.157×** | ✅ |
| short fuzz 1,500 | — | **0 mismatch** |

这是关键差异：v6 在长行 adversarial 上 **0.962×（略慢）**，kernel 候选仍有 **1.157×**，没有为了短行 benchmark 牺牲通用性。

## 机制

候选给每条正则加了 **provably necessary literal prefilter**：

- `Bearer` → 没出现就直接跳过；
- `sk-or-v1-` / `sk-orca-` / `sk-` / `ghp_` 同理；
- `named_secret` 用 `key/token/secret/password + [:=]` 的轻量 hint 先筛；
- 非 ASCII 文本回退到 exact `(?i)` gate，避免 Unicode case-fold 差异；
- 命中后再走原来的有序 pattern pipeline。

因此它不是按行切分，也不是只对 benchmark 形状有效；它是“先证明不可能匹配，再跑正则”。

## 运行中的异常

这一代 PRAXIST frontier 只记录了 baseline，没有把 peer0 的候选写入 canonical frontier：

- peer0 在 `peer_workspaces/.../gated_prefilter_v1` 产出了完整 evaluator summary；
- peer1 被 delete guard 挡住，最后只留下 `gen0_peer1_redaction_original.py`；
- 因此本报告的 4.86× 来自 **peer0 的实际 evaluator summary + 我手工复核**，不是 frontier 自动晋升。

这也是下一步要修的编排问题：候选必须被 canonical frontier 捕获，不能只留在 peer workspace。

## 状态

- promotion 记录：`proposed`，未自动批准；
- 已通过 54/55 + fuzz 0 + held-out exact；
- 建议人工审批前，再跑一次独立复现。

## 文件

- `gen0_eval.json` — peer0 evaluator summary
- `gen0_candidate.py` — 候选 `redaction.py`
- `candidate.patch` — 相对 pristine 的 diff
- `holdout_benchmark.json` / `holdout_audit.json`
- `run_report.md` / `run_summary.json` / `gen0_boundary.json`
- `promotions.jsonl` / `curve.svg` / `curve.json`
