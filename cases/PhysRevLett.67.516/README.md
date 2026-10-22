# PhysRevLett.67.516: Coherent Destruction of Tunneling

Preprint: **No preprint recorded as of 2026-10-22**

Published as: [Coherent Destruction of Tunneling](https://doi.org/10.1103/PhysRevLett.67.516)

Formal citation: Phys. Rev. Lett. 67, 516 (1991) · DOI `10.1103/PhysRevLett.67.516` · Locator `516`

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

完整双阱模型重现相干隧穿抑制，无需两能级替代。

![Independently generated overview](outputs/figures/fig1-independent.png)

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
| Declared source targets | 完整双阱模型重现相干隧穿抑制，无需两能级替代。 | [PNG](outputs/figures/fig1-independent.png) | [JSON](outputs/checks/numerical-checks.json) |

### Declared source targets: 完整双阱模型重现相干隧穿抑制，无需两能级替代。

![Declared source targets reproduction](outputs/figures/fig1-independent.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/PhysRevLett.67.516/code/requirements.txt
cd cases/PhysRevLett.67.516/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 两个驱动位置的重合标记无法分辨多重性；没有把其余长时间曲线和密度像素比较自动判为完成。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
