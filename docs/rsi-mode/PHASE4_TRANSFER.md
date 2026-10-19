# Phase 4 — Transfer A/B 结果

**结论：B 组（RSI-hardened）在“达到 bo_score ≥ 1.5 的时间”和总 wall-clock 上明显更快，但最终分数只高 1.05%，没有达到预注册的 +10%。这是一次“流程迁移部分有效”的结果，不是“RSI 让新课题自动更强”的证明。**

## 任务

黑箱实验设计：6 个合成函数，4 个 6D 非中心最优点 + branin + hartmann3；每个函数 3 个 seed，每次 60 次评估。

```text
bo_score = 1 + correctness_rate × mean_normalized_gain
random baseline = 1.0
perfect = 2.0
```

## 结果

| 指标 | A stock | B RSI-hardened | 差异 |
|---|---:|---:|---:|
| peers × generations | 4 × 4 | 4 × 4 | 相同 |
| 有效候选数 | 24 | **47** | +96% |
| 最终 best `bo_score` | 1.854888 | **1.874299** | **+1.05%** |
| 首次 ≥1.5 | 4.86 min | **2.26 min** | **−53.5%** |
| 总 wall-clock | 65.55 min | **51.17 min** | **−21.9%** |
| protocol violations | 0 | 0 | 相同 |

### 每代 best

| 代 | A stock | B hardened |
|---|---:|---:|
| gen 0 | 1.740246 | **1.874299** |
| gen 1 | 1.793688 | 1.827624 |
| gen 2 | 1.854888 | 1.874299 |
| gen 3 | 1.854888 | 1.874299 |

## 预注册标准判定

| 标准 | 结果 |
|---|---|
| B 最终 score 比 A 高 ≥10% | ❌ 只有 +1.05% |
| B 达到 `bo_score ≥ 1.5` 的时间/成本低 ≥20% | ✅ 4.86 → 2.26 min，约 −53.5% |
| protocol violations = 0 | ✅ 两边都是 0 |

**判定：时间门槛通过，分数门槛未通过。**

## 这意味着什么

### 支持的结论

- RSI-hardened 的流程能让研究循环**更快进入有效区间**；
- 它产生了更多候选（47 vs 24），探索更充分；
- 总 wall-clock 低约 22%；
- 没有协议违规。

### 不支持的结论

- **没有 4 代能力复利**：B 的最佳值在 gen0 就出现了，gen1 还回退，gen2/3 只是复现同一分数；
- **没有最终分数显著提升**：+1.05%，低于预注册的 10%；
- **不能外推为通用 RSI**：只有一个任务、一次 A/B、合成函数、mtime 计时。

## 诚实的解释

B 的优势更像：

> **更快找到一个好候选，并更早停止无效探索。**

而不是：

> **每一代都比上一代更强。**

这符合当前原型的定位：我们改的是研究流程（时间盒、quorum、canonical capture），不是模型权重，也不是通用研究能力。流程减少了空转和早停错误，但没有自动创造更强的算法。

## 下一步

1. 用第二个 transfer 任务重复 A/B，确认“时间优势”不是这个任务的偶然；
2. 加 held-out seeds / functions，看最终分数差异是否稳定；
3. 把 operator contract 标准化，再做第二个前端 Agent 的无损驱动验证；
4. 在这些验证完成前，对外只说“子系统级 RSI 原型 + 流程优化”，不说“通用 RSI”。

## 文件

- `ab_metrics.json` — 全部聚合指标
- `A_STOCK/` — run summary、frontier、best eval/candidate
- `B_HARDENED/` — 同上
- `task/` — 评估器、baseline、prompts
- `TASK_DESIGN.md` — 预注册设计
