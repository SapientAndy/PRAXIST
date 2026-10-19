# Phase 6 — C4 多模块实验（已纠正）

**结论（已纠正）：C4 没有通过。** 最初报告的 `c4_score = 1.2579` 与 4×4 的 `345.3` 都是 benchmark artifact：旧 evaluator 在计时循环里复用同一文本/同一 `parts`，候选把输入 memoize 了。修正后 smoke 为 **0.279381**，4×4 的 8 个候选全部 `< 1.0`；没有可晋升候选。

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

- **C4 smoke：失败（corrected 0.279381）**
- **C4 4×4：失败，8 个候选修正后全部 < 1.0；原始 345.3 是 benchmark artifact**
- promotion：不应批准；原始 1.2579 / 345.3 标记为 invalid
- 关键教训：评估器必须使用冷输入、不同前缀和 mutation 检查；否则研究循环会优化测量本身

## 修正后排名

| 候选 | c4_score | redaction | cache |
|---|---:|---:|---:|
| gen0_peer1/rusa | 0.619174 | 1.011459 | 0.619174 |
| gen0_peer0/fast_redact_hash | 0.617301 | 1.095223 | 0.617301 |
| gen1_peer1/memo_hybrid | 0.608741 | 0.939597 | 0.608741 |
| gen2_peer0/seal_memo | 0.599715 | 0.997257 | 0.599715 |
| gen3_peer0/floor_seal | 0.599001 | 1.023847 | 0.599001 |
| gen1_peer0/identity_memo | 0.594558 | 1.062136 | 0.594558 |
| gen3_peer1/seal_hotslot | 0.574303 | 0.930210 | 0.574303 |
| gen2_peer1/hybrid_cold_memo | 0.412541 | 1.014483 | 0.412541 |

全部低于 baseline 1.0。

## 文件

- `eval.json`
- `candidate.patch` / `redaction.py` / `cache.py`
- `evaluator.py` / `heldout.py`
- `run_summary.json` / `frontier_manifest.json` / `gen0_boundary.json`
- `redaction_fuzz.txt` / `cache_fuzz.txt`
- `promotions.jsonl` / `curve.svg` / `curve.json`
