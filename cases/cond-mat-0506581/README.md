# cond-mat-0506581: Quantum Spin Hall Effect and Topological Phase Transition in HgTe Quantum Wells

Preprint: [cond-mat/0506581v2 — Quantum Spin Hall Effect and Topological Phase Transition in HgTe Quantum Wells](https://arxiv.org/abs/cond-mat/0506581)

Formal publication: **Not recorded as of 2026-10-24**

Public status: **Scientific reproduction — main physical results reproduced** · Audit score: **Not assessed / 未评分**

Kane-Mele 锯齿能带、Pfaffian 拓扑判据和扭边界零点结构得到独立模型支持。

![Independently generated overview](outputs/figures/wilson_check.png)

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
| Declared source targets | Kane-Mele 锯齿能带、Pfaffian 拓扑判据和扭边界零点结构得到独立模型支持。 | [PNG](outputs/figures/wilson_check.png) | [JSON](outputs/checks/numerical-checks.json) |

### Declared source targets: Kane-Mele 锯齿能带、Pfaffian 拓扑判据和扭边界零点结构得到独立模型支持。

![Declared source targets reproduction](outputs/figures/wilson_check.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r cases/cond-mat-0506581/code/requirements.txt
cd cases/cond-mat-0506581/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: 示意图面板按科学内容核验，不做像素级复刻；相互作用扩展保留为原文的猜想层级。

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
