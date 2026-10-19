# Phase 6 — C4 多模块 RSI Smoke

**结论：C4 smoke 通过。候选同时改了两个 PRAXIST 模块，`c4_score = 1.2579`，held-out 7/7，redaction 1.258×，cache 1.774×。**

这是第一次不是“只改一个 redaction.py”的候选。

## 任务

- 候选：完整 `workspace/praxist/` 包副本
- 允许修改任意模块
- 评分同时看两个模块：

```text
c4_score =
  in_scope_pass_rate
  × heldout_rate
  × min(redaction_speedup, cache_speedup)
```

- sealed tests：55，54 通过
- 外部 held-out：7 项，位于 task project 之外
- 1 peer × 1 generation（smoke）

## 结果

| 指标 | 数值 |
|---|---:|
| `c4_score` | **1.257916** |
| `in_scope_pass_rate` | 1.0 |
| `heldout_rate` | **1.0（7/7）** |
| redaction speedup | **1.257916×** |
| cache speedup | **1.773597×** |
| redaction median | 3.7931 ms |
| cache median | 189.4016 ms |
| 外部 redaction fuzz | **0/1,200** |
| 外部 cache fuzz | **0/1,500** |

frontier 自动记录：

```text
gen0_peer0/fastred_fastcache
c4_score = 1.257916
source = results/gen0_peer0/fastred_fastcache/evaluation_summary.json
```

## 改动

候选改了至少两个模块：

- `praxist/core/redaction.py`
- `praxist/core/cache.py`

完整 diff：

- `candidate.patch`
- `redaction.py`
- `cache.py`

## 验证

- sealed tests：54/55，in-scope failures 0
- held-out：7/7
- redaction 外部差分 fuzz：0/1,200
- cache 外部差分 fuzz：0/1,500
- RSI boundary：`rsi_ready=true`
- 运行的 evaluator 和 held-out 都在 candidate workspace 之外

## 状态

- promotion：`proposed`，未自动批准
- 这次是 1 peer × 1 generation 的 **C4 smoke**，不是完整 4×4 证据
- 仍需更大规模复现、更多 held-out 任务、人工审批后，才能说“C4 完整通过”

## 文件

- `eval.json`
- `candidate.patch` / `redaction.py` / `cache.py`
- `evaluator.py` / `heldout.py`
- `run_summary.json` / `frontier_manifest.json` / `gen0_boundary.json`
- `redaction_fuzz.txt` / `cache_fuzz.txt`
- `promotions.jsonl` / `curve.svg` / `curve.json`
