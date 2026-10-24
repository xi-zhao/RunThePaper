# 1805.06492: Bulk-boundary correspondence in non-Hermitian systems

Preprint: [1805.06492v2 — Bulk-boundary correspondence in non-Hermitian systems](https://arxiv.org/abs/1805.06492)

Formal publication: **Not recorded as of 2026-10-24**

Public status: **Scientific reproduction — main physical results reproduced** · Audit score: **Not assessed / 未评分**

非厄米 SSH/Rice-Mele 精确边界谱、biorthogonal 极化与开放/周期临界差异得到独立支持。

![Independently generated overview](outputs/figures/F1-reproduced.png)

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Final same-agent report](docs/FINAL-REPORT.md)
- [Numerical methods and rerun scope](docs/NUMERICAL_METHODS.md)
- [Recorded boundaries](docs/LESSONS_LEARNED.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Declared source targets | 非厄米 SSH/Rice-Mele 精确边界谱、biorthogonal 极化与开放/周期临界差异得到独立支持。 | [PNG](outputs/figures/F1-reproduced.png) | [JSON](outputs/checks/numerical-checks.json) |

## Paper Reference vs Independent Reproduction

Comparison reference: arXiv:1805.06492v2. Panels contain independently generated results and any limited attributed source marks are excluded from repository content license. Visual agreement does not establish author-data equality; original figures and digitized point sets are not redistributed.

### F2-reproduced comparison

![F2-reproduced paper reference versus independent reproduction](docs/comparisons/F2-reproduced.png)

### Declared source targets: 非厄米 SSH/Rice-Mele 精确边界谱、biorthogonal 极化与开放/周期临界差异得到独立支持。

![Declared source targets reproduction](outputs/figures/F1-reproduced.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1805.06492/code/requirements.txt
cd cases/1805.06492/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 1 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: 有限尺度和指数弱端耦合控制支持声明范围，不外推为所有参数平面的一般证明。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
