# Phase 2 — Held-out 验证：83× 是真的，但不是“任意文本 83×”

**结论：v6 候选在 held-out 语料上输出与 hits 全部 exact，没有语义回归；但速度收益强烈依赖负载形状。**

## 1. Benchmark 形状、换随机种子

任务 benchmark 是 12,000 行、每 11 行一条 `Bearer ... sk-...`、约 95 万字符。用同样的生成器换种子：

| 语料 | 字符数 | 基线 | v6 候选 | 加速 | exact |
|---|---:|---:|---:|---:|---|
| seed 43 | 945,245 | 94.447 ms | 1.400 ms | **67.5×** | ✅ |
| seed 44 | 943,829 | 103.530 ms | 1.520 ms | **68.1×** | ✅ |

## 2. 同形状、改变密钥密度

| 语料 | 密钥频率 | 基线 | v6 候选 | 加速 | exact |
|---|---:|---:|---:|---:|---|
| dense seed 45 | 每 3 行 | 96.495 ms | 5.943 ms | **16.2×** | ✅ |
| sparse seed 46 | 每 31 行 | 111.915 ms | 0.813 ms | **137.7×** | ✅ |

越稀疏收益越大，符合“按行预筛、只对候选行跑正则”的机制。

## 3. 长行 / 跨行 / 对抗形状

| 语料 | 字符数 | 基线 | v6 候选 | 加速 | exact |
|---|---:|---:|---:|---:|---|
| sparse long-line | 2,000,015 | 223.990 ms | 223.572 ms | 1.002× | ✅ |
| dense long-line | 1,000,001 | 156.120 ms | 145.069 ms | 1.076× | ✅ |
| adversarial long-line | 800,048 | 96.143 ms | 99.963 ms | **0.962×** | ✅ |
| short fuzz (1,500) | — | — | — | — | **0 mismatch** |

长行语料里每行本身就很长，按行预筛的收益被摊薄；对抗语料里保守 fallback 触发得更多，甚至略慢于基线。

## 结论

- **正确性可以泛化**：所有 held-out 语料和 1,500 条新 fuzz 都是 exact；
- **速度不能泛化成一个固定倍数**：83.5× 应表述为“在 benchmark 形状的短行负载上约 83×”，不能说“redaction 通用快 83×”；
- v6 仍然是安全候选，但它的能力指标必须带负载条件。

## 对 RSI 的含义

这次 held-out 证明研究循环没有靠改测试或输出作弊，但也暴露了**单指标 + 单一负载形状会被优化到局部最优**。下一步不能继续在同一 benchmark 上堆代，而应该：

1. 把“同形状 held-out + 长行 held-out”都纳入评分，形成双门槛；
2. 只有两个门槛都过的候选才能进入 promotion；
3. 再把同一套 candidate/evaluator/promotion 结构推广到 kernel 级多模块候选。

## 文件

- `holdout_benchmark_shape.json` — 同形状/变密度结果
- `holdout_shape_audit.json` — 长行/对抗/短 fuzz 结果
- `holdout_benchmark.py` — 同形状 held-out 生成器
- `holdout_audit.py` — 长行/对抗审计器
- `v6_candidate.py` / `pristine_redaction.py`
