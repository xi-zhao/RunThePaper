# 2412.14271: Dissipative Phase Transition in the Two-Photon Dicke Model

Preprint: [arXiv:2412.14271 — Dissipative Phase Transition in the Two-Photon Dicke Model](https://arxiv.org/abs/2412.14271)

Published as: [Dissipative Phase Transition in the Two-Photon Dicke Model](https://doi.org/10.1103/mz92-6l9g)

Formal citation: 135, 173602 (2025) · DOI `10.1103/mz92-6l9g` · Locator `173602`

Public status: **Partial scientific reproduction** · Audit score: **46.71/100**

Atomic numerical coverage is 29/31 (93.55%); the old 7/8 figure described implementation groups, not paper items.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Independent paper assessment](docs/PAPER_ASSESSMENT.md)
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
cd cases/2412.14271/code
python scripts/run_reproduction.py --config config/analytic.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Main quantum figures are feature-level because trajectory counts are reduced. Formal Supplement Fig. S3 is an explicit uncovered item because its panel inventory, observable, and parameters are unavailable. Formal Supplement Fig. S4 is an explicit uncovered item because its panel inventory, observable, and parameters are unavailable. Fig. 3(g)/Fig. S2 has a confirmed branch-to-spectrum evidence discrepancy: the plotted lower branch is nonlinearly unstable but has no positive Bogoliubov eigenvalue.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2](outputs/figures/fig2.png)

![fig3](outputs/figures/fig3.png)

![fig4](outputs/figures/fig4.png)

![figS1](outputs/figures/figS1.png)

![figS2](outputs/figures/figS2.png)

![figS5](outputs/figures/figS5.png)

![figS parity](outputs/figures/figS_parity.png)
