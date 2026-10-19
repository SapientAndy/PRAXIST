# Phase 3e — Fastgate（v6 候选，当前最佳）

**结论：v6 从 5.6319 ms 降到 5.2022 ms，1.0826×；54/55 测试保持；外部 fuzz 0/1,200；held-out 相对 pristine 10.7–22.0×，长行 1.33–1.40×。PRAXIST frontier 自动捕获。**

## 任务内结果

| 指标 | 数值 |
|---|---:|
| 测试 | 54/55，in-scope failures 0 |
| baseline | 5.6319 ms |
| 候选 median | **5.2022 ms** |
| speedup | **1.0826×** |
| 外部 fuzz | **0/1,200** |

frontier：

```text
gen0_peer0/fastgate
deterministic_score = 1.082608
source = results/gen0_peer0/fastgate/evaluation_summary.json
```

## Held-out

| 语料 | 相对 pristine | exact |
|---|---:|---|
| seed 43 | **19.336×** | ✅ |
| seed 44 | **21.047×** | ✅ |
| dense | **10.698×** | ✅ |
| sparse | **22.049×** | ✅ |
| 长行 sparse | 1.330× | ✅ |
| 长行 dense | 1.402× | ✅ |
| 长行 adversarial | 1.386× | ✅ |
| short fuzz 1,500 | — | 0 mismatch |

## Kernel-copy 总曲线

```text
pristine:          87.9 ms
v1 kernel:         18.08 ms  (4.86×)
v3 named hint:     10.19 ms  (1.817×)
v4 literal span:    6.92 ms  (1.472×)
v5 fused literal:   5.63 ms  (1.229×)
v6 fastgate:        5.20 ms  (1.083×)
```

相对 pristine 约 **16.9×**；相对 v1 kernel 候选约 **3.5×**。

## 停止理由

v6 的相对提升是 8.3%，仍高于 5% 停止线；但绝对收益只有 **0.43 ms**，且已经进入 benchmark 噪声与实现复杂度的边际区。继续 v7 的收益很可能小于审计成本，因此这里停下，把 v6 作为当前最佳候选。

## 状态

- promotion：`proposed`，未自动批准；
- 已通过 54/55 + fuzz 0 + held-out exact；
- canonical capture 连续 v4/v5/v6 正常工作；
- 下一步是人工审批/独立复现，而不是继续刷同一 benchmark。

## 文件

- `eval.json`
- `candidate.py` / `candidate.patch`
- `holdout_benchmark.json` / `holdout_audit.json`
- `run_summary.json` / `gen0_boundary.json`
- `promotions.jsonl` / `curve.svg` / `curve.json`
