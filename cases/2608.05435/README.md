# 2608.05435: Experimental demonstration of the Quantum Fourier Transform on up to 100 qubits using a convolutional compilation strategy

Preprint: [arXiv:2608.05435v2 — Experimental demonstration of the Quantum Fourier Transform on up to 100 qubits using a convolutional compilation strategy](https://arxiv.org/abs/2608.05435v2)

Formal publication: **Not recorded as of 2026-11-15**

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

用矩阵和百比特门串复算卷积 QFT。100 比特三档构造用 590 个 CX，28 组小规模矩阵的最大差为 8.17×10⁻¹⁶。

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
| Circuit identity and Table I | 用矩阵和百比特门串复算卷积 QFT。100 比特三档构造用 590 个 CX，28 组小规模矩阵的最大差为 8.17×10⁻¹⁶。 | [PNG](outputs/figures/overview.png) | [JSON](outputs/checks/numerical-checks.json) |

### Circuit identity and Table I: 用矩阵和百比特门串复算卷积 QFT。100 比特三档构造用 590 个 CX，28 组小规模矩阵的最大差为 8.17×10⁻¹⁶。

![Circuit identity and Table I reproduction](outputs/figures/overview.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/2608.05435/code/requirements.txt
cd cases/2608.05435/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 缺原实机样本、物理排程和相位校验。理想线路等价性与实机性能分开报告。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
