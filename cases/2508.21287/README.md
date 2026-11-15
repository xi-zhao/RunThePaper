# 2508.21287: Δ-Motif: Parallel Subgraph Isomorphism via Tabular Operations for Scalable Layout Selection

Preprint: [arXiv:2508.21287v4 — Δ-Motif: Parallel Subgraph Isomorphism via Tabular Operations for Scalable Layout Selection](https://arxiv.org/abs/2508.21287v4)

Formal publication: **Not recorded as of 2026-11-15**

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

用路径表连接和独立穷举复得图 2 的 28 个候选与 12 个有效映射。三点路径在三角形上有 6 个保边单射，诱导匹配为 0。

![Independently generated overview](outputs/figures/overview.png)

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [推导 / Derivation](docs/DERIVATION.md)
- [复算 / Rerun](docs/NUMERICAL_METHODS.md)
- [资料缺口 / Data availability](docs/DATA-AVAILABILITY.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Figure 2 and matching semantics | 用路径表连接和独立穷举复得图 2 的 28 个候选与 12 个有效映射。三点路径在三角形上有 6 个保边单射，诱导匹配为 0。 | [PNG](outputs/figures/overview.png) | [JSON](outputs/checks/numerical-checks.json) |

### Figure 2 and matching semantics: 用路径表连接和独立穷举复得图 2 的 28 个候选与 12 个有效映射。三点路径在三角形上有 6 个保边单射，诱导匹配为 0。

![Figure 2 and matching semantics reproduction](outputs/figures/overview.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2508.21287/code/requirements.txt
cd cases/2508.21287/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: H200 和原硬件对照仍需对应环境与精确输入。公开运行核验算法和计数。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
