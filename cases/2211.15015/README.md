# 2211.15015: Discontinuous Shear Thickening in Biological Tissue Rheology

Preprint: [arXiv:2211.15015 — Discontinuous Shear Thickening in Biological Tissue Rheology](https://arxiv.org/abs/2211.15015)

Published as: [Discontinuous Shear Thickening in Biological Tissue Rheology](https://doi.org/10.1103/PhysRevX.14.011027)

Formal citation: Phys. Rev. X 14, 011027 (2024) · DOI `10.1103/PhysRevX.14.011027` · Locator `011027`

Public status: **Partial scientific reproduction** · Audit score: **0.00/100**

The complete paper contains 135 eligible atomic items. Two analytic force claims are reproduced, 131 items are objectively compute-blocked, and two convergence claims reached an evidenced system capability limit; no item remains pending.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Paper review protocol](docs/PAPER_REVIEW_PROTOCOL_V2.md)
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

### T011 source vs reproduction comparison

![T011 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T011_source_vs_reproduction.png)

### T012 source vs reproduction comparison

![T012 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T012_source_vs_reproduction.png)

### T013 source vs reproduction comparison

![T013 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T013_source_vs_reproduction.png)

### T014 source vs reproduction comparison

![T014 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T014_source_vs_reproduction.png)

### T015 source vs reproduction comparison

![T015 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T015_source_vs_reproduction.png)

### T016 source vs reproduction comparison

![T016 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T016_source_vs_reproduction.png)

### T017 source vs reproduction comparison

![T017 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T017_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2211.15015/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 17 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: All 17 numerical panels in Main Figures 2--7 are independent simulation targets; Main Figure 1 and Appendix Figure 8 are schematics. The author code is available only on request and was neither requested nor accessed. No author numerical arrays or source pixels are scientific inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T029 green kubo vs rheology](outputs/figures/claim_feature/T029_green_kubo_vs_rheology.png)

![T030 p0 double star scan](outputs/figures/claim_feature/T030_p0_double_star_scan.png)

![T001 main fig2a flow solid](outputs/figures/feature/T001_main_fig2a_flow_solid.png)

![T002 main fig2b flow liquid](outputs/figures/feature/T002_main_fig2b_flow_liquid.png)

![T003 main fig3a viscosity activity](outputs/figures/feature/T003_main_fig3a_viscosity_activity.png)

![T004 main fig3b viscosity map](outputs/figures/feature/T004_main_fig3b_viscosity_map.png)

![T005 main fig4a dst curve](outputs/figures/feature/T005_main_fig4a_dst_curve.png)

![T006 main fig4b stress strain](outputs/figures/feature/T006_main_fig4b_stress_strain.png)

![T007 main fig4c stress distribution](outputs/figures/feature/T007_main_fig4c_stress_distribution.png)

![T008 main fig4d low tension network](outputs/figures/feature/T008_main_fig4d_low_tension_network.png)

![T009 main fig4e high tension network](outputs/figures/feature/T009_main_fig4e_high_tension_network.png)

![T010 main fig5 onset scaling](outputs/figures/feature/T010_main_fig5_onset_scaling.png)

![T011 main fig6 phase map](outputs/figures/feature/T011_main_fig6_phase_map.png)

![T012 main fig6i yield](outputs/figures/feature/T012_main_fig6i_yield.png)

![T013 main fig6ii cst](outputs/figures/feature/T013_main_fig6ii_cst.png)

![T014 main fig6iii dst](outputs/figures/feature/T014_main_fig6iii_dst.png)

![T015 main fig6iv newtonian](outputs/figures/feature/T015_main_fig6iv_newtonian.png)

![T016 main fig7a scaled curves](outputs/figures/feature/T016_main_fig7a_scaled_curves.png)

![T017 main fig7b peclet relation](outputs/figures/feature/T017_main_fig7b_peclet_relation.png)

![T018 fig2a newtonian fits](outputs/figures/feature/T018_fig2a_newtonian_fits.png)

![T019 fig2b newtonian fits](outputs/figures/feature/T019_fig2b_newtonian_fits.png)

![T020 fig3a fit families](outputs/figures/feature/T020_fig3a_fit_families.png)

![T021 fig3b vc boundary](outputs/figures/feature/T021_fig3b_vc_boundary.png)

![T022 fig5 power law fits](outputs/figures/feature/T022_fig5_power_law_fits.png)

![T023 fig6 top thickening loss](outputs/figures/feature/T023_fig6_top_thickening_loss.png)

![T024 fig7b linear guide](outputs/figures/feature/T024_fig7b_linear_guide.png)
