# Phase 3b — Named-secret fast path（v3 候选）

**结论：候选把 kernel baseline 从 18.5207 ms 降到 10.1908 ms，1.8174×；54/55 测试保持；外部 fuzz 0/1,200；held-out 相对 pristine 8.4–8.9×，长行 1.11–1.21×。**

## 任务内结果

| 指标 | 数值 |
|---|---:|
| 测试 | 54/55，in-scope failures 0 |
| baseline | 18.5207 ms |
| 候选 median | **10.1908 ms** |
| speedup | **1.8174×** |
| 外部 fuzz | **0/1,200** |

## Held-out

同形状、换种子：

| 语料 | 相对 pristine | exact |
|---|---:|---|
| seed 43 | **8.401×** | ✅ |
| seed 44 | **8.838×** | ✅ |
| dense | **7.759×** | ✅ |
| sparse | **8.898×** | ✅ |

长行 / 对抗：

| 语料 | 相对 pristine | exact |
|---|---:|---|
| 长行 sparse | 1.205× | ✅ |
| 长行 dense | 1.108× | ✅ |
| 长行 adversarial | 1.165× | ✅ |
| short fuzz 1,500 | — | 0 mismatch |

## 机制

候选把 `_NAMED_SECRET_HINT_ASCII.search(text.lower())` 这条 **11.3 ms** 的整段小写 + 正则扫描，替换成 `str.find` 的精确等价实现：

- 先找 `key/token/secret/password` 后的 `:` / `=`；
- 再处理反引号 `key\`...\`` 形式；
- 非 ASCII 文本回退到原来的 `(?i)` 路径；
- 因为返回 `False` 仍然是“不可能匹配”的必要条件，输出和 hits 不变。

这是对父代机制的直接改进，不是重写。

## 编排问题

v3 的 generation 在第 1 分钟被 `mature_quorum` 关闭：

- peer1 的 baseline（score 1.000792）被自动算成成熟结果；
- quorum 满足后，peer0 的候选被冻结；
- 候选从未被 PRAXIST 评估，只留在 `variants/`。

所以 1.8174× 来自 **我手工运行 sealed evaluator + 外部 fuzz/held-out**，不是 frontier 自动晋升。候选文件、eval、patch、held-out 都在本目录。

## 状态

- promotion：`proposed`，未自动批准；
- 已通过 54/55 + fuzz 0 + held-out exact；
- 绝对速度优于 Phase 3 的 18.08 ms 候选（10.19 ms）。

## 文件

- `eval.json` — sealed evaluator summary
- `candidate.py` — 候选 `redaction.py`
- `candidate.patch`
- `holdout_benchmark.json` / `holdout_audit.json`
- `run_summary.json` / `gen0_boundary.json`
