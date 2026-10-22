# cond-mat-0606236: Effect of Suddenly Turning on Interactions in the Luttinger Model

Preprint: [arXiv:cond-mat/0606236v2 — Effect of Suddenly Turning on Interactions in the Luttinger Model](https://arxiv.org/abs/cond-mat/0606236v2)

Published as: [Effect of Suddenly Turning on Interactions in the Luttinger Model](https://doi.org/10.1103/PhysRevLett.97.156403)

Formal citation: Phys. Rev. Lett. 97, 156403 (2006) · DOI `10.1103/PhysRevLett.97.156403` · Locator `156403`

Public status: **Scientific reproduction — main physical results reproduced** · Audit score: **Not assessed / 未评分**

淬火后的非热稳态幂律、有限尺寸复现和 GGE 两点函数得到支持。

![Independently generated overview](outputs/figures/analytic-checks.png)

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [简短图文报告 / Illustrated report](docs/report/index.html)
- [推导 / Derivation](docs/DERIVATION.md)
- [复算与范围 / Rerun and scope](docs/NUMERICAL_METHODS.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Declared source targets | 淬火后的非热稳态幂律、有限尺寸复现和 GGE 两点函数得到支持。 | [PNG](outputs/figures/analytic-checks.png) | [JSON](outputs/checks/numerical-checks.json) |

### Declared source targets: 淬火后的非热稳态幂律、有限尺寸复现和 GGE 两点函数得到支持。

![Declared source targets reproduction](outputs/figures/analytic-checks.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-0606236/code/requirements.txt
cd cases/cond-mat-0606236/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 数值样例支持指定公式，不能代替对所有无限维物理状态的一般性证明。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
