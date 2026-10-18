# Phase 1e — Redaction v5：从 spanmerge 安全 parent 继续

**结论：从 v4 的 `gen1_peer1_spanmerge_lb_next` 再跑 3 代，得到 1.2498× 相对提升（1.7453 ms → 1.3965 ms），29/29 正确，外部 fuzz 0/1,200。相对原始模块约 72.3×。**

## 曲线

| 代 | 候选 | 正确性 | 中位耗时 | 相对 v4 parent |
|---|---|---|---:|---:|
| baseline | `gen1_peer1_spanmerge_lb_next` | 29/29 | 1.7453 ms | 1.0000 |
| gen 2 | `gen2_peer1_c` | 29/29 | **1.3965 ms** | **1.2498** |

## 验证

- 29 个 sealed cases 全部通过；
- external differential fuzz：0 output mismatch / 0 hit mismatch（1,200 cases）；
- `protected_manifest.json` 哈希校验通过；
- 只改 `workspace/redaction.py` 的副本；
- promotion 记录为 `proposed`，没有自动批准。

## 累计曲线

```text
pristine: 100.9227 ms
v2 safe span_slice: 14.8998 ms → 3.319×
v3 gated: 2.8721 ms → 1.563×
v4 spanmerge: 1.7453 ms → 1.646×
v5 c: 1.3965 ms → 1.250×
```

相对原始模块累计约 **72.3×**，每一轮都保持 29/29 + fuzz 0/1,200。

## 边界

- 仍是子系统级 RSI，不是 kernel 级 RSI；
- benchmark 仍为合成、in-distribution；
- 没有 held-out 公开基准；
- 目标、指标、baseline、审批仍由人给。

## 复现

```bash
cd /home/andyl/PraxistExamples/praxist_redaction_speed_v5
python3 evaluations/run.py --workspace experiments/run_v5_direct_1/variants/gen2_peer1_c
python3 /home/andyl/diff_fuzz.py
```
