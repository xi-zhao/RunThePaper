# 1910.00020: Scalable probes of measurement-induced criticality

Preprint: [arXiv:1910.00020v2 — Scalable probes of measurement-induced criticality](https://arxiv.org/abs/1910.00020)

Published as: [Scalable Probes of Measurement-Induced Criticality](https://doi.org/10.1103/PhysRevLett.125.070606)

Formal citation: 125, 070606 (2020) · DOI `10.1103/PhysRevLett.125.070606` · Locator `070606`

Public status: **Partial scientific reproduction** · Audit score: **69.34/100**

All numerical panels are independently generated with an exact partial-record channel; reduced scale and unpublished sampling metadata prevent paper-exact status.

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1910.00020/code
python scripts/run_reproduction.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 8 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Every target is independently generated from a phase-free binary stabilizer simulation; no author code, numerical arrays, or source pixels enter the runner. Published system sizes and unknown Monte Carlo metadata are reduced; Fig. 2(b) now uses exact mixed-stabilizer conditioning for an incomplete record. Fresh-context independent review remains pending.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig1b transition](outputs/figures/T001_main_fig1b_transition.png)

![T002 main fig2a lightcone](outputs/figures/T002_main_fig2a_lightcone.png)

![T003 main fig2b cutoff decoder](outputs/figures/T003_main_fig2b_cutoff_decoder.png)

![T004 main fig3a surface order](outputs/figures/T004_main_fig3a_surface_order.png)

![T005 main fig3b cylinder](outputs/figures/T005_main_fig3b_cylinder.png)

![T006 main fig3c strip](outputs/figures/T006_main_fig3c_strip.png)

![T007 supp figS1 lightcones](outputs/figures/T007_supp_figS1_lightcones.png)

![T008 supp figS2 purification](outputs/figures/T008_supp_figS2_purification.png)
