# Phase 1d — Redaction v4：从 gateskip 安全 parent 继续

**结论：从 v3 的 `gen2_peer1_gateskip` 再跑 3 代，得到 1.6456× 相对提升（2.8721 ms → 1.7453 ms），29/29 正确，外部 fuzz 0/1,200。相对原始模块约 57.8×。**

## 曲线

| 代 | 候选 | 正确性 | 中位耗时 | 相对 v3 parent |
|---|---|---|---:|---:|
| baseline | `gen2_peer1_gateskip` | 29/29 | 2.8721 ms | 1.0000 |
| gen 1 | `gen1_peer0_sortedspans_pair2` | 29/29 | 2.1069 ms | 1.3632 |
| gen 2 | `gen1_peer1_spanmerge_lb_next` | 29/29 | **1.7453 ms** | **1.6456** |

## 验证

- 29 个 sealed cases 全部通过；
- external differential fuzz：0 output mismatch / 0 hit mismatch（1,200 cases）；
- `protected_manifest.json` 哈希校验通过；
- 只改 `workspace/redaction.py` 的副本；
- promotion 记录为 `proposed`，没有自动批准。

## 意义

v1：找到快解，但跨行不保真，被审计拦下。  
v2：从安全 `span_slice` 继续，3.319×，fuzz 0。  
v3：从 gated 继续，1.563×，fuzz 0。  
v4：从 gateskip 继续，1.646×，fuzz 0。

四轮都通过了 29/29 + fuzz 0，说明这不是一次偶然，而是同一安全 gate 下连续多轮可复现的子系统提升。

## 边界

- 仍是子系统级 RSI，不是 kernel 级 RSI；
- benchmark 仍为合成、in-distribution；
- 没有 held-out 公开基准；
- 目标、指标、baseline、审批仍由人给。

## 复现

```bash
cd /home/andyl/PraxistExamples/praxist_redaction_speed_v4
python3 evaluations/run.py --workspace experiments/run_v4_direct_1/variants/gen1_peer1_spanmerge_lb_next
python3 /home/andyl/diff_fuzz.py
```
