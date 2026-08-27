# 2401.05830: Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit

Preprint: [arXiv:2401.05830 — Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit](https://arxiv.org/abs/2401.05830)

Published as: [Inverse Mpemba Effect Demonstrated on a Single Trapped Ion Qubit](https://doi.org/10.1103/PhysRevLett.133.010403)

Formal citation: Physical Review Letters 133, 010403 (2024) · DOI `10.1103/PhysRevLett.133.010403` · Locator `Vol. 133, Issue 1, article 010403`

Public status: **Scientific reproduction — paper-error candidates identified** · Audit score: **90.00/100**

The arXiv v2 PDF contains the accepted manuscript and Supplemental Material.

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

### T001 source vs reproduction comparison

![T001 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T001_source_vs_reproduction.png)

### T002 source vs reproduction comparison

![T002 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T002_source_vs_reproduction.png)

### T003 source vs reproduction comparison

![T003 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T003_source_vs_reproduction.png)

### T004 source vs reproduction comparison

![T004 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T004_source_vs_reproduction.png)

### T005 source vs reproduction comparison

![T005 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T005_source_vs_reproduction.png)

### T006 source vs reproduction comparison

![T006 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T006_source_vs_reproduction.png)

### T007 source vs reproduction comparison

![T007 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T007_source_vs_reproduction.png)

### T008 source vs reproduction comparison

![T008 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T008_source_vs_reproduction.png)

### T009 source vs reproduction comparison

![T009 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T009_source_vs_reproduction.png)

### T010 source vs reproduction comparison

![T010 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T010_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2401.05830/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 10 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Author source code and numerical arrays are outside the allowed evidence boundary.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig2 left](outputs/figures/T001_main_fig2_left.png)

![T002 main fig2 right](outputs/figures/T002_main_fig2_right.png)

![T003 main fig4 theory](outputs/figures/T003_main_fig4_theory.png)

![T004 supp fig1](outputs/figures/T004_supp_fig1.png)

![T005 supp fig2](outputs/figures/T005_supp_fig2.png)

![T006 supp fig3](outputs/figures/T006_supp_fig3.png)

![T007 supp fig4 left](outputs/figures/T007_supp_fig4_left.png)

![T008 supp fig4 right](outputs/figures/T008_supp_fig4_right.png)

![T009 supp fig5 left](outputs/figures/T009_supp_fig5_left.png)

![T010 supp fig5 right](outputs/figures/T010_supp_fig5_right.png)
