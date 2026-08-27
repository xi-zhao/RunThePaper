# 2402.14814: Realization of a Laughlin State of Two Rapidly Rotating Fermions

Preprint: [arXiv:2402.14814v2 — Realization of a Laughlin State of Two Rapidly Rotating Fermions](https://arxiv.org/abs/2402.14814)

Published as: [Realization of a Laughlin State of Two Rapidly Rotating Fermions](https://doi.org/10.1103/PhysRevLett.133.253401)

Formal citation: Phys. Rev. Lett. 133, 253401 (2024) · DOI `10.1103/PhysRevLett.133.253401` · Locator `253401`

Public status: **Partial scientific reproduction** · Audit score: **83.83/100**

All formula-derived theory regions are implemented independently.

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

### T018 source vs reproduction comparison

![T018 source vs reproduction paper reference versus independent reproduction](docs/comparisons/T018_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2402.14814/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 18 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Experimental samples are not digitized and are recorded as missing_author_data. Supplement Fig. S2 uses a runnable reconstructed interaction model because the paper omits the complete coupled-channel and drive calibration inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig2a levels](outputs/figures/T001_main_fig2a_levels.png)

![T002 main fig2d rabi](outputs/figures/T002_main_fig2d_rabi.png)

![T003 main fig3a theory](outputs/figures/T003_main_fig3a_theory.png)

![T004 main fig3b theory](outputs/figures/T004_main_fig3b_theory.png)

![T005 main fig4a radial](outputs/figures/T005_main_fig4a_radial.png)

![T006 main fig4b radial](outputs/figures/T006_main_fig4b_radial.png)

![T007 main fig4c angle](outputs/figures/T007_main_fig4c_angle.png)

![T008 supp figs1 levels](outputs/figures/T008_supp_figs1_levels.png)

![T009 supp figs2 harmonic](outputs/figures/T009_supp_figs2_harmonic.png)

![T010 supp figs2 anharmonic](outputs/figures/T010_supp_figs2_anharmonic.png)

![T011 supp figs2c driven spectrum](outputs/figures/T011_supp_figs2c_driven_spectrum.png)

![T012 supp figs3 laughlin](outputs/figures/T012_supp_figs3_laughlin.png)

![T013 supp figs3 noninteracting](outputs/figures/T013_supp_figs3_noninteracting.png)

![T014 supp figs3 center of mass](outputs/figures/T014_supp_figs3_center_of_mass.png)

![T015 supp figs3f density evolution](outputs/figures/T015_supp_figs3f_density_evolution.png)

![T016 supp figs4 azimuthal](outputs/figures/T016_supp_figs4_azimuthal.png)

![T017 supp figs6 spin down](outputs/figures/T017_supp_figs6_spin_down.png)

![T018 supp figs6 spin up](outputs/figures/T018_supp_figs6_spin_up.png)
