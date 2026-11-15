# 2511.21831: No need to calibrate: characterization and compilation for high-fidelity circuit execution using imperfect gates

Preprint: [arXiv:2511.21831v1 — No need to calibrate: characterization and compilation for high-fidelity circuit execution using imperfect gates](https://arxiv.org/abs/2511.21831v1)

Formal publication: **Not recorded as of 2026-11-15**

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

分块指数和直接指数验证交叉共振模型。两脉冲与三脉冲回代保留原门条件，三脉冲补写的 514 个实例最大矩阵误差 2.26×10⁻¹⁵。

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
| Two- and three-pulse constructions | 分块指数和直接指数验证交叉共振模型。两脉冲与三脉冲回代保留原门条件，三脉冲补写的 514 个实例最大矩阵误差 2.26×10⁻¹⁵。 | [PNG](outputs/figures/overview.png) | [JSON](outputs/checks/numerical-checks.json) |

### Two- and three-pulse constructions: 分块指数和直接指数验证交叉共振模型。两脉冲与三脉冲回代保留原门条件，三脉冲补写的 514 个实例最大矩阵误差 2.26×10⁻¹⁵。

![Two- and three-pulse constructions reproduction](outputs/figures/overview.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2511.21831/code/requirements.txt
cd cases/2511.21831/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 缺原门校准和逐次测量，图 8 改善倍数仍受观测量与图注口径影响。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
