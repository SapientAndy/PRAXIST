# Phase 3d — Fused-literal fast path（v5 候选）

**结论：v5 从 6.9212 ms 降到 5.6319 ms，1.2289×；54/55 测试保持；外部 fuzz 0/1,200；held-out 相对 pristine 11.6–23.0×，长行 1.38–1.46×。PRAXIST frontier 自动捕获。**

## 任务内结果

| 指标 | 数值 |
|---|---:|
| 测试 | 54/55，in-scope failures 0 |
| baseline | 6.9212 ms |
| 候选 median | **5.6319 ms** |
| speedup | **1.2289×** |
| 外部 fuzz | **0/1,200** |

frontier：

```text
gen0_peer1/fused_literal
deterministic_score = 1.228936
source = results/gen0_peer1/fused_literal/evaluation_summary.json
```

## Held-out

| 语料 | 相对 pristine | exact |
|---|---:|---|
| seed 43 | **16.633×** | ✅ |
| seed 44 | **18.252×** | ✅ |
| dense | **11.601×** | ✅ |
| sparse | **22.964×** | ✅ |
| 长行 sparse | 1.380× | ✅ |
| 长行 dense | 1.460× | ✅ |
| 长行 adversarial | 1.416× | ✅ |
| short fuzz 1,500 | — | 0 mismatch |

## 累计 kernel-copy 曲线

```text
pristine:       87.9 ms
v1 kernel:      18.08 ms  4.86×
v3 named hint:  10.19 ms  1.817×
v4 literal span: 6.92 ms  1.472×
v5 fused literal:5.63 ms  1.229×
```

相对 pristine 约 **15.6×**；相对 v1 kernel 候选约 **3.2×**。

## 状态

- promotion：`proposed`，未自动批准；
- 已通过 54/55 + fuzz 0 + held-out exact；
- 这是当前最快且泛化最好的安全候选；
- 另外，v4/v5 两代都由 frontier 自动捕获，canonical capture 与 quorum 修复都已验证。

## 文件

- `eval.json`
- `candidate.py` / `candidate.patch`
- `holdout_benchmark.json` / `holdout_audit.json`
- `run_summary.json` / `gen0_boundary.json`
- `promotions.jsonl` / `curve.svg` / `curve.json`
