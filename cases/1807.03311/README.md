# 1807.03311: Topological insulators in twisted transition metal dichalcogenide homobilayers

Preprint: [arXiv:1807.03311 — Topological insulators in twisted transition metal dichalcogenide homobilayers](https://arxiv.org/abs/1807.03311)

Published as: [Topological Insulators in Twisted Transition Metal Dichalcogenide Homobilayers](https://doi.org/10.1103/PhysRevLett.122.086402)

Formal citation: Phys. Rev. Lett. 122, 086402 (2019) · DOI `10.1103/PhysRevLett.122.086402` · Locator `122, 086402`

Public status: **Partial scientific reproduction** · Audit score: **70.00/100**

Eleven executable numerical regions are formula-derived; two external first-principles DFT panels remain explicitly deferred.

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1807.03311/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 11 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Independent numerical run attested in a raw/reference-free sandbox.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig2b pseudospin](outputs/figures/T001_main_fig2b_pseudospin.png)

![T002 main fig3a bands](outputs/figures/T002_main_fig3a_bands.png)

![T003 main fig3b dos](outputs/figures/T003_main_fig3b_dos.png)

![T004 main fig3c berry](outputs/figures/T004_main_fig3c_berry.png)

![T005 main fig4a bands](outputs/figures/T005_main_fig4a_bands.png)

![T006 main fig4b gaps](outputs/figures/T006_main_fig4b_gaps.png)

![T007 main fig4c phase](outputs/figures/T007_main_fig4c_phase.png)

![T008 supp dirac valence](outputs/figures/T008_supp_dirac_valence.png)

![T009 supp dirac conduction](outputs/figures/T009_supp_dirac_conduction.png)

![T010 supp spin 1p2](outputs/figures/T010_supp_spin_1p2.png)

![T011 supp spin 2p0](outputs/figures/T011_supp_spin_2p0.png)
