# 1804.03151: Hubbard model physics in transition metal dichalcogenide moire bands

Preprint: [arXiv:1804.03151 — Hubbard model physics in transition metal dichalcogenide moire bands](https://arxiv.org/abs/1804.03151)

Published as: [Hubbard model physics in transition metal dichalcogenide moire bands](https://doi.org/10.1103/PhysRevLett.121.026402)

Formal citation: Phys. Rev. Lett. 121, 026402 (2018) · DOI `10.1103/PhysRevLett.121.026402` · Locator `026402`

Public status: **Partial scientific reproduction** · Audit score: **70.00/100**

Twelve executable numerical regions are formula-derived; one under-specified DFT panel remains explicitly deferred.

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

### T005 side by side comparison

![T005 side by side paper reference versus independent reproduction](docs/comparisons/T005_side_by_side.png)

### T006 side by side comparison

![T006 side by side paper reference versus independent reproduction](docs/comparisons/T006_side_by_side.png)

### T007 side by side comparison

![T007 side by side paper reference versus independent reproduction](docs/comparisons/T007_side_by_side.png)

### T008 side by side comparison

![T008 side by side paper reference versus independent reproduction](docs/comparisons/T008_side_by_side.png)

### T009 side by side comparison

![T009 side by side paper reference versus independent reproduction](docs/comparisons/T009_side_by_side.png)

### T010 side by side comparison

![T010 side by side paper reference versus independent reproduction](docs/comparisons/T010_side_by_side.png)

### T011 side by side comparison

![T011 side by side paper reference versus independent reproduction](docs/comparisons/T011_side_by_side.png)

### T012 side by side comparison

![T012 side by side paper reference versus independent reproduction](docs/comparisons/T012_side_by_side.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1804.03151/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 12 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Main Figure 1(c) is explicitly deferred because the exact DFT environment is under-specified. The numerical runner is isolated from paper-source figures and author numerical artifacts.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig1d potential](outputs/figures/T001_main_fig1d_potential.png)

![T002 main fig2a bands](outputs/figures/T002_main_fig2a_bands.png)

![T003 main fig2b dos](outputs/figures/T003_main_fig2b_dos.png)

![T004 main fig2c wannier](outputs/figures/T004_main_fig2c_wannier.png)

![T005 main fig2d hopping](outputs/figures/T005_main_fig2d_hopping.png)

![T006 main fig3a interactions](outputs/figures/T006_main_fig3a_interactions.png)

![T007 main fig3b exchange](outputs/figures/T007_main_fig3b_exchange.png)

![T008 main fig4a fermi contour](outputs/figures/T008_main_fig4a_fermi_contour.png)

![T009 supp fig5a potential](outputs/figures/T009_supp_fig5a_potential.png)

![T010 supp fig5b bands](outputs/figures/T010_supp_fig5b_bands.png)

![T011 supp fig5c hopping](outputs/figures/T011_supp_fig5c_hopping.png)

![T012 supp fig5d interactions](outputs/figures/T012_supp_fig5d_interactions.png)
