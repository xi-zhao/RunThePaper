# 2409.18176: Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach Resonances

Preprint: [arXiv:2409.18176 — Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach Resonances](https://arxiv.org/abs/2409.18176)

Published as: [Tuning Transport in Solid-State Bose-Fermi Mixtures by Feshbach Resonances](https://doi.org/10.1103/PhysRevLett.134.126502)

Formal citation: Phys. Rev. Lett. 134, 126502 (2025) · DOI `10.1103/PhysRevLett.134.126502` · Locator `126502`

Public status: **Partial scientific reproduction** · Audit score: **54.90/100**

The arXiv paper and source archive were frozen before implementation.

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

### comparison contact comparison

![comparison contact paper reference versus independent reproduction](docs/comparisons/comparison_contact.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2409.18176/code
python scripts/run_reproduction.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 11 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Author numerical arrays and source pixels were not used as scientific inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig1b scattering](outputs/figures/T001_main_fig1b_scattering.png)

![T002 main fig1c resistivity](outputs/figures/T002_main_fig1c_resistivity.png)

![T003 main fig2 exciton drag](outputs/figures/T003_main_fig2_exciton_drag.png)

![T004 main fig3 temperature](outputs/figures/T004_main_fig3_temperature.png)

![T005 main fig3 inset](outputs/figures/T005_main_fig3_inset.png)

![T006 main fig4a ac hole](outputs/figures/T006_main_fig4a_ac_hole.png)

![T007 main fig4b ac exciton](outputs/figures/T007_main_fig4b_ac_exciton.png)

![T008 main fig4c ac trion](outputs/figures/T008_main_fig4c_ac_trion.png)

![T009 supp fig6 kubo difference](outputs/figures/T009_supp_fig6_kubo_difference.png)

![T010 supp fig7 trion drag](outputs/figures/T010_supp_fig7_trion_drag.png)
