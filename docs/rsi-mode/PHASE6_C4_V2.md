# C4 v2 — Anti-Cheat Rerun Results

**结论：C4 v2 没有通过。没有可晋升候选。**

## 运行

```text
task:        praxist_c4_v2
peers:       4
generations: 4
status:      succeeded
frontier:    6 records
candidates:  12
```

C4 v2 的 evaluator：

- 每次计时使用新 redaction 文本；
- cache 使用 100 个不同前缀；
- 外部 held-out 8 项 + storage 4 项；
- 新增空列表、空 dict、空字符串、mutation 语义检查。

## 候选审计

### 1. `framecanon` — 分数最高，但语义错误

原始 frontier：

```text
gen3_peer1/framecanon
c4_score = 1.276144
redaction_speedup = 1.276144
cache_speedup = 1.395306
held-out = 8/8
```

加入空容器检查后：

```text
frozen_prefix_hash([])
baseline:  sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
candidate: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**空列表哈希错误。拒绝。**

### 2. `bincanon` — 分数第二，fuzz 失败

```text
c4_score = 1.126823
redaction_speedup = 1.126823
cache_speedup = 1.802199
```

外部 cache fuzz：

```text
cases=1500 cache_mismatches=3
```

典型：

```text
[{"k0": -132}]
[{"k0": "beta", "k1": 705, ...}]
[{"k0": "alpha", "k1": "line1\r\nline2"}]
```

**语义不一致。拒绝。**

### 3. `hashlean` — 语义干净，但没有稳定提升

```text
原始单次: c4_score = 1.026084
redaction_speedup = 1.237199
cache_speedup = 1.026084
```

外部检查：

```text
redaction fuzz: 0/1,200
cache fuzz:     0/1,500
held-out:       11/11
storage:        4/4
```

但五次独立重测：

| run | c4_score | redaction | cache |
|---|---:|---:|---:|
| 0 | 0.998310 | 1.206156 | 0.998310 |
| 1 | 0.901256 | 1.175756 | 0.901256 |
| 2 | 0.986125 | 1.207777 | 0.986125 |
| 3 | 0.979180 | 1.061546 | 0.979180 |
| 4 | 0.980815 | 1.213279 | 0.980815 |

```text
median = 0.980815
mean   = 0.969137
```

**没有稳定超过 baseline 1.0。拒绝。**

## 结论

C4 v2 证明了：

1. 防缓存版 evaluator 能工作；
2. 候选仍会找到新的“优化测量”路径（身份/结构 memo、空容器特例）；
3. 只有在语义 fuzz、空容器、mutation、重复测量都通过后，才可能谈晋升；
4. 目前没有候选同时满足“两个模块真实提升 + 语义正确 + 可复现”。

**C4 v2：失败。promotion：0。**

## 文件

- `run_summary.json` / `frontier_manifest.json`
- `framecanon_eval.json` / `framecanon_cache_fuzz.txt`
- `bincanon_eval.json` / `bincanon_cache_fuzz.txt`
- `hashlean_eval.json` / `hashlean_5runs.json`
- `hashlean_fuzz_redaction.txt` / `hashlean_fuzz_cache.txt`
- `heldout.py` / `evaluator.py`
