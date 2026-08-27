# 2512.23799: Efficient simulation of logical magic state preparation protocols

Preprint: [arXiv:2512.23799 — Efficient simulation of logical magic state preparation protocols](https://arxiv.org/abs/2512.23799)

Published as: [Efficient Simulation of Logical Magic State Preparation Protocols](https://doi.org/10.1103/fby6-xjbm)

Formal citation: PRX Quantum 7, 020329 (2026) · DOI `10.1103/fby6-xjbm` · Locator `020329`

Public status: **Partial scientific reproduction** · Audit score: **59.11/100**

A source-free literal-circuit Steane implementation and sampling test were rerun in isolation. T001-T002 are attempted numerical mismatches, T003 reaches a proven publication benchmark boundary, and T004 reproduces the inverse-square-root sampling law.

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
cd cases/2512.23799/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Numerical benchmark figures are proxy checks only because the exact Steane circuit and benchmark parameters have not been run.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1 infidelity reproduction](outputs/figures/fig1_infidelity_reproduction.png)

![fig2 acceptance reproduction](outputs/figures/fig2_acceptance_reproduction.png)

![fig3 runtime reproduction](outputs/figures/fig3_runtime_reproduction.png)

![fig4 sampling precision reproduction](outputs/figures/fig4_sampling_precision_reproduction.png)

![steane exact acceptance](outputs/figures/steane_exact_acceptance.png)

![steane exact infidelity](outputs/figures/steane_exact_infidelity.png)
