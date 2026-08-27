# 2502.20558: Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms

Preprint: [arXiv:2502.20558 — Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms](https://arxiv.org/abs/2502.20558)

Published as: [Leveraging Qubit Loss Detection in Fault-Tolerant Quantum Algorithms](https://doi.org/10.1103/ycwc-3myc)

Formal citation: Phys. Rev. X 16, 011002 (2026) · DOI `10.1103/ycwc-3myc` · Locator `011002`

Public status: **Partial scientific reproduction** · Audit score: **79.31/100**

Case scaffolded from framework/templates/paper_case.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2502.20558/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: All 272 eligible atomic items have final evidence-backed dispositions: 26 reproduced, 1 externally blocked, and 245 attempted but not reproduced. Similarity score 79.31/100; strict lifecycle remains partial and the central circuit-level surface-code scope reached the current clean-room capability limit.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig14c swap lifecycles](outputs/figures/fig14c_swap_lifecycles.png)

![fig16a lifecycle comparison](outputs/figures/fig16a_lifecycle_comparison.png)

![fig2b proxy](outputs/figures/fig2b_proxy.png)

![fig4b lifecycle threshold](outputs/figures/fig4b_lifecycle_threshold.png)

![fig6b algorithm lifecycles](outputs/figures/fig6b_algorithm_lifecycles.png)
