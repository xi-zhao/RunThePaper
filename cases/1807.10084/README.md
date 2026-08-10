# 1807.10084: Nonreciprocal Photon Blockade

Preprint: [arXiv:1807.10084 — Nonreciprocal Photon Blockade](https://arxiv.org/abs/1807.10084)

Published as: [Nonreciprocal Photon Blockade](https://doi.org/10.1103/PhysRevLett.121.153601)

Formal citation: Physical Review Letters 121, 153601 (2018) · DOI `10.1103/PhysRevLett.121.153601` · Locator `153601`

Public status: **Scientific reproduction — visual review pending** · Audit score: **82.24/100**

Case scaffolded from framework/templates/paper_case.

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

### T001 main fig1 full comparison

![T001 main fig1 full paper reference versus independent reproduction](docs/comparisons/T001_main_fig1_full.png)

### T002 main fig2 full comparison

![T002 main fig2 full paper reference versus independent reproduction](docs/comparisons/T002_main_fig2_full.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1807.10084/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 2 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: All numerical subfigures are in scope; mixed schematics retain only formula-derived theoretical content. Original figures are reference-only. Author code and author numerical arrays are prohibited inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 levels](outputs/figures/main_fig1_levels.png)

![main fig2](outputs/figures/main_fig2.png)

![main fig3 abc](outputs/figures/main_fig3_abc.png)

![main fig3d](outputs/figures/main_fig3d.png)

![main fig4](outputs/figures/main_fig4.png)

![supp fig s1](outputs/figures/supp_fig_s1.png)

![supp fig s2](outputs/figures/supp_fig_s2.png)

![supp fig s3](outputs/figures/supp_fig_s3.png)

![supp fig s4](outputs/figures/supp_fig_s4.png)

![supp fig s5](outputs/figures/supp_fig_s5.png)

![supp fig s6](outputs/figures/supp_fig_s6.png)

![supp fig s7](outputs/figures/supp_fig_s7.png)

![supp fig s8](outputs/figures/supp_fig_s8.png)

![supp fig s9](outputs/figures/supp_fig_s9.png)
