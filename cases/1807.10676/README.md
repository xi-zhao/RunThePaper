# 1807.10676: All "Magic Angles" Are "Stable" Topological

Preprint: [arXiv:1807.10676v2 — All "Magic Angles" Are "Stable" Topological](https://arxiv.org/abs/1807.10676)

Published as: [All "Magic Angles" Are "Stable" Topological](https://doi.org/10.1103/PhysRevLett.123.036401)

Formal citation: 123, 036401 (2019) · DOI `10.1103/PhysRevLett.123.036401` · Locator `036401`

Public status: **Partial scientific reproduction** · Audit score: **69.77/100**

Forty-two executable numerical subpanels are formula-derived; the licensed DFT campaign remains explicitly deferred.

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
cd cases/1807.10676/code
python scripts/run_reproduction.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 12 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Twelve DFT numerical entries are explicitly deferred for insufficient compute/license inputs. Fresh-context independent review remains pending.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 main fig1a velocity](outputs/figures/T001_main_fig1a_velocity.png)

![T002 main fig1b wilson](outputs/figures/T002_main_fig1b_wilson.png)

![T003 main fig2b tb4 bands](outputs/figures/T003_main_fig2b_tb4_bands.png)

![T004 main fig2c tb4 wilson](outputs/figures/T004_main_fig2c_tb4_wilson.png)

![T005 supp fig2a levels](outputs/figures/T005_supp_fig2a_levels.png)

![T006 supp fig3 bands](outputs/figures/T006_supp_fig3_bands.png)

![T007 supp fig4a gamma levels](outputs/figures/T007_supp_fig4a_gamma_levels.png)

![T008 supp fig5 magic generation](outputs/figures/T008_supp_fig5_magic_generation.png)

![T009 supp fig6 ph breaking](outputs/figures/T009_supp_fig6_ph_breaking.png)

![T010 supp fig7 wilson](outputs/figures/T010_supp_fig7_wilson.png)

![T011 supp fig9 tb8](outputs/figures/T011_supp_fig9_tb8.png)

![T012 supp fig10 tb4 2v](outputs/figures/T012_supp_fig10_tb4_2v.png)

![contact sheet](outputs/figures/contact_sheet.png)
