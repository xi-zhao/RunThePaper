# 1904.07225: Adaptive characterization of spatially inhomogeneous fields and errors in qubit registers

Preprint: [arXiv:1904.07225v2 — Autonomous adaptive noise characterization in quantum computers](https://arxiv.org/abs/1904.07225v2)

Published as: [Adaptive characterization of spatially inhomogeneous fields and errors in qubit registers](https://doi.org/10.1038/s41534-020-0286-0)

Formal citation: npj Quantum Inf 6, 53 (2020) · DOI `10.1038/s41534-020-0286-0` · Locator `53`

Public status: **Partial scientific reproduction** · Audit score: **Not assessed / 未评分**

固定参数下，NMQA 在五个低预算点胜过直接计频的均匀抽样。对同一计数施加 Jeffreys 平滑后，两种分组的九个预算点均由均匀对照取得较低的留出预测误差。

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
| Figure 4 and six-ion held-out scores | 固定参数下，NMQA 在五个低预算点胜过直接计频的均匀抽样。对同一计数施加 Jeffreys 平滑后，两种分组的九个预算点均由均匀对照取得较低的留出预测误差。 | [PNG](outputs/figures/overview.png) | [JSON](outputs/checks/numerical-checks.json) |

### Figure 4 and six-ion held-out scores: 固定参数下，NMQA 在五个低预算点胜过直接计频的均匀抽样。对同一计数施加 Jeffreys 平滑后，两种分组的九个预算点均由均匀对照取得较低的留出预测误差。

![Figure 4 and six-ion held-out scores reproduction](outputs/figures/overview.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/1904.07225/code/requirements.txt
cd cases/1904.07225/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 这里的 Brier 分数评估公开读出的预测。原 SSIM 倍数仍需同期逐次地图和制图设置。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
