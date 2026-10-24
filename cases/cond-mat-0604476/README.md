# cond-mat-0604476: Relaxation of an Isolated Interacting Fermion System by a Generalized Gibbs Ensemble

Preprint: [cond-mat/0604476v2 — Relaxation of an Isolated Interacting Fermion System by a Generalized Gibbs Ensemble](https://arxiv.org/abs/cond-mat/0604476)

Formal publication: **Not recorded as of 2026-10-24**

Public status: **Scientific reproduction — main physical results reproduced** · Audit score: **Not assessed / 未评分**

箱势阱展开与周期四超晶格淬火的 GGE 预测、边界控制和长时间动量分布得到独立支持。

![Independently generated overview](outputs/figures/momentum-gge.png)

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
| Declared source targets | 箱势阱展开与周期四超晶格淬火的 GGE 预测、边界控制和长时间动量分布得到独立支持。 | [PNG](outputs/figures/momentum-gge.png) | [JSON](outputs/checks/numerical-checks.json) |

### Declared source targets: 箱势阱展开与周期四超晶格淬火的 GGE 预测、边界控制和长时间动量分布得到独立支持。

![Declared source targets reproduction](outputs/figures/momentum-gge.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-0604476/code/requirements.txt
cd cases/cond-mat-0604476/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 数值样例和边界控制支持声明范围，不构成对无限维一般物理状态的形式证明。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
