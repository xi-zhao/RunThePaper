# 1202.5532: Growth of entanglement entropy in a free-fermion model

Preprint: [1202.5532v3 — Growth of entanglement entropy in a free-fermion model](https://arxiv.org/abs/1202.5532)

Formal publication: **Not recorded as of 2026-10-24**

Public status: **Scientific reproduction — main physical results reproduced** · Audit score: **Not assessed / 未评分**

弱相互作用下对数纠缠增长、体积律饱和、粒子数涨落控制和自由费米映射得到独立数值支持。

![Independently generated overview](outputs/figures/entanglement-growth.png)

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
| Declared source targets | 弱相互作用下对数纠缠增长、体积律饱和、粒子数涨落控制和自由费米映射得到独立数值支持。 | [PNG](outputs/figures/entanglement-growth.png) | [JSON](outputs/checks/numerical-checks.json) |

### Declared source targets: 弱相互作用下对数纠缠增长、体积律饱和、粒子数涨落控制和自由费米映射得到独立数值支持。

![Declared source targets reproduction](outputs/figures/entanglement-growth.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1202.5532/code/requirements.txt
cd cases/1202.5532/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 有限尺寸与数值收敛边界保留；熵律外推不是热力学无限系统的形式证明。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
