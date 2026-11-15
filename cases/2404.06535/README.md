# 2404.06535: Learning to rank quantum circuits for hardware-optimized performance enhancement

Preprint: [arXiv:2404.06535v2 — Learning to rank quantum circuits for hardware-optimized performance enhancement](https://arxiv.org/abs/2404.06535v2)

Published as: [Learning to rank quantum circuits for hardware-optimized performance enhancement](https://doi.org/10.22331/q-2024-11-27-1542)

Formal citation: Quantum 8, 1542 (2024) · DOI `10.22331/q-2024-11-27-1542` · Locator `1542`

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

逐门重算公开布局并核对九种训练损失。在有配对标签的公开子集上，最佳选择误差 7.60%，Mapomatic 12.85%。

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
| Table 2 ranking losses | 逐门重算公开布局并核对九种训练损失。在有配对标签的公开子集上，最佳选择误差 7.60%，Mapomatic 12.85%。 | [PNG](outputs/figures/overview.png) | [JSON](outputs/checks/numerical-checks.json) |

### Table 2 ranking losses: 逐门重算公开布局并核对九种训练损失。在有配对标签的公开子集上，最佳选择误差 7.60%，Mapomatic 12.85%。

![Table 2 ranking losses reproduction](outputs/figures/overview.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2404.06535/code/requirements.txt
cd cases/2404.06535/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 缺历史学习划分、误差缓解标签及原硬件作业，原宣传倍率未完成核验。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
