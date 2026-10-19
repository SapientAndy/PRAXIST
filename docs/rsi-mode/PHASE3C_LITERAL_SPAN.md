# Phase 3c — Literal-span fast path（v4 候选）

**结论：v4 从 10.1908 ms 降到 6.9212 ms，1.4724×；54/55 测试保持；外部 fuzz 0/1,200；held-out 相对 pristine 12.3–21.9×，长行 1.35–1.39×。这次 PRAXIST frontier 自动捕获了候选。**

## 任务内结果

| 指标 | 数值 |
|---|---:|
| 测试 | 54/55，in-scope failures 0 |
| baseline | 10.1908 ms |
| 候选 median | **6.9212 ms** |
| speedup | **1.4724×** |
| 外部 fuzz | **0/1,200** |

`frontier_manifest.json` 记录：

```text
gen0_peer0/literal_span
deterministic_score = 1.472406
source = results/gen0_peer0/literal_span/evaluation_summary.json
```

这是第一次 **canonical capture 正常工作**，不再依赖手工搬结果。

## Held-out

同形状、换种子：

| 语料 | 相对 pristine | exact |
|---|---:|---|
| seed 43 | **19.629×** | ✅ |
| seed 44 | **19.649×** | ✅ |
| dense（每 3 行） | **12.306×** | ✅ |
| sparse（每 31 行） | **21.905×** | ✅ |

长行 / 对抗：

| 语料 | 相对 pristine | exact |
|---|---:|---|
| 长行 sparse | 1.345× | ✅ |
| 长行 dense | 1.391× | ✅ |
| 长行 adversarial | 1.379× | ✅ |
| short fuzz 1,500 | — | 0 mismatch |

## 机制

v4 在 v3 的 named-secret `str.find` 基础上，继续减少 `sk-` 的 `subn` 成本，使用字面量 span / 精确 prefilter；完整 diff 见 `candidate.patch`。

关键点：

- 不按行切分，所以长行仍能保持 >1.3×；
- 所有 held-out 输出与 hits exact；
- 1,500 条新 fuzz 0 mismatch。

## 编排修复

v4 的 prompt 要求：

- baseline 只写到 `/tmp`，不写 `results/`；
- 只有候选结果写 canonical `results/<peer_id>/<name>/`。

结果：baseline 没有触发 mature quorum，v4 在约 6 分钟后产出候选，frontier 自动记录 `gen0_peer0/literal_span`。

## 状态

- promotion：`proposed`，未自动批准；
- 已通过 54/55 + fuzz 0 + held-out exact；
- 当前最佳绝对速度：**6.9212 ms**，相对 pristine 约 **12.7×**；
- 相对 v1 kernel 候选（18.08 ms）约 **2.6×**。

## 文件

- `eval.json`
- `candidate.py` / `candidate.patch`
- `holdout_benchmark.json` / `holdout_audit.json`
- `run_summary.json` / `gen0_boundary.json`
- `promotions.jsonl` / `curve.svg` / `curve.json`
