# 1809.03452: Qiskit Backend Specifications for OpenQASM and OpenPulse Experiments

Preprint: [arXiv:1809.03452v1 — Qiskit Backend Specifications for OpenQASM and OpenPulse Experiments](https://arxiv.org/abs/1809.03452v1)

Formal publication: **Not recorded as of 2026-11-10**

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

图 4 六个轴已重建，四条滤波路径的 1,397 个矢量点符合绘图精度。独立模拟了 Bell、隐形传态和重复码，另定位历史 Qobj 引用、寄存器类型与脉冲时序差异。

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
| Figure 4, Qobj examples and exact circuit controls | 图 4 六个轴已重建，四条滤波路径的 1,397 个矢量点符合绘图精度。独立模拟了 Bell、隐形传态和重复码，另定位历史 Qobj 引用、寄存器类型与脉冲时序差异。 | [PNG](outputs/figures/overview.png) | [JSON](outputs/checks/numerical-checks.json) |

### Figure 4, Qobj examples and exact circuit controls: 图 4 六个轴已重建，四条滤波路径的 1,397 个矢量点符合绘图精度。独立模拟了 Bell、隐形传态和重复码，另定位历史 Qobj 引用、寄存器类型与脉冲时序差异。

![Figure 4, Qobj examples and exact circuit controls reproduction](outputs/figures/overview.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1809.03452/code/requirements.txt
cd cases/1809.03452/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 历史实机配置未公开。公开入口重算 10 μs 方波基准和 Bell 对照，论文矢量点与 Qobj 原样文件保留原来源。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
