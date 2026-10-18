# Phase 1c — Redaction v3：从 gated 安全 parent 继续

**结论：从 v2 的 `gen1_peer1_gated` 再跑 3 代，得到 1.563× 相对提升（4.4892 ms → 2.8721 ms），29/29 正确，外部 fuzz 0/1,200。相对原始模块约 35×。**

## 曲线

| 代 | 候选 | 正确性 | 中位耗时 | 相对 v2 parent | 相对 pristine |
|---|---|---|---:|---:|---:|
| baseline | `gen1_peer1_gated` | 29/29 | 4.4892 ms | 1.0000 | ≈22.5× |
| gen 1 | `gen1_peer0_sepgate` | 29/29 | 3.6885 ms | 1.2171 | — |
| gen 2 | `gen2_peer1_gateskip` | 29/29 | **2.8721 ms** | **1.5630** | **≈35.1×** |

## 验证

- 29 个 sealed cases 全部通过；
- external differential fuzz：0 output mismatch / 0 hit mismatch（1,200 cases）；
- `protected_manifest.json` 哈希校验通过；
- 候选只改 `workspace/redaction.py` 的副本；
- `promotions.jsonl` 中记录为 `proposed`，没有自动批准。

## 意义

v1：从原始模块找到快解，但跨行密钥不保真，被外部审计拦下。  
v2：从安全 `span_slice` 继续，得到 3.319× 相对提升，29/29 + fuzz 0。  
v3：从 v2 的 gated 安全候选继续，再得到 1.563× 相对提升，29/29 + fuzz 0。

这说明：**在安全 gate 下，研究循环可以连续多轮改进同一个子系统，而不是只能找到一次快解。**

## 边界

- 仍是子系统级 RSI，不是 PRAXIST kernel 级 RSI；
- benchmark 仍为合成、in-distribution；
- 目标、指标、baseline、审批仍是人给的；
- 没有 held-out 公开基准，v3 的 29 cases 与 v2 相同，存在过拟合风险。

## 复现

```bash
cd /home/andyl/PraxistExamples/praxist_redaction_speed_v3
python3 evaluations/run.py --workspace experiments/run_v3_direct_1/variants/gen2_peer1_gateskip
python3 /home/andyl/diff_fuzz.py
```
