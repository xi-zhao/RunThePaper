# 1803.07128: Quantum machine learning in feature Hilbert spaces

Preprint: [arXiv:1803.07128v1 — Quantum machine learning in feature Hilbert spaces](https://arxiv.org/abs/1803.07128)

Published as: [Quantum Machine Learning in Feature Hilbert Spaces](https://doi.org/10.1103/PhysRevLett.122.040504)

Formal citation: 122, 040504 (2019) · DOI `10.1103/PhysRevLett.122.040504` · Locator `040504`

Public status: **Scientific reproduction — paper-error candidates identified** · Audit score: **66.00/100**

Four display targets cover fourteen numerical items; the independent Appendix B-D claim is implemented and reveals qualified source-discrepancy candidates pending fresh review.

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

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### T001 side by side comparison

![T001 side by side paper reference versus independent reproduction](docs/comparisons/T001_side_by_side.png)

### T002 side by side comparison

![T002 side by side paper reference versus independent reproduction](docs/comparisons/T002_side_by_side.png)

### T003 side by side comparison

![T003 side by side paper reference versus independent reproduction](docs/comparisons/T003_side_by_side.png)

### T004 side by side comparison

![T004 side by side paper reference versus independent reproduction](docs/comparisons/T004_side_by_side.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install scikit-learn torch
cd cases/1803.07128/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 4 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Fig. 4 is paper-exact; Fig. 5--8 use printed methods with declared reconstructed metadata because seeds and critical training details are absent. Fresh-context independent review remains pending.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 fig4 squeezing kernel](outputs/figures/T001_fig4_squeezing_kernel.png)

![T002 fig5 svm boundaries](outputs/figures/T002_fig5_svm_boundaries.png)

![T003 fig6 fock perceptron](outputs/figures/T003_fig6_fock_perceptron.png)

![T004 fig8 variational classifier](outputs/figures/T004_fig8_variational_classifier.png)
