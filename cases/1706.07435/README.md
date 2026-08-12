# 1706.07435: Topological Band Theory for Non-Hermitian Hamiltonians

Preprint: [arXiv:1706.07435 — Topological Band Theory for Non-Hermitian Hamiltonians](https://arxiv.org/abs/1706.07435)

Published as: [Topological Band Theory for Non-Hermitian Hamiltonians](https://doi.org/10.1103/PhysRevLett.120.146402)

Formal citation: Phys. Rev. Lett. 120, 146402 (2018) · DOI `10.1103/PhysRevLett.120.146402` · Locator `146402`

Public status: **Partial scientific reproduction** · Audit score: **90.00/100**

Independently derives and numerically reproduces all 15 theory-numerical panels across Main Figs. 1-3 and Supplement Figs. 2-4: complex bulk and domain-wall spectra, exceptional-point sheet exchange and half vorticity, phase boundaries and opposite charges, paper-exact cylinder spectra, and hybrid directional exponents. All generated arrays come from formulas or independent eigensolvers; paper pixels are downstream visual-audit inputs only.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Main Fig. 1 | Complex bulk sheets and independently matched localized domain-wall branch | [PNG](outputs/figures/main_fig1_reproduction.png) | [JSON](outputs/checks/t001_scientific_checks.json) |
| Main Fig. 2(a-c) | Exceptional-point sheets, loop branch exchange, half vorticity, and square-root cut | [PNG](outputs/figures/main_fig2_reproduction.png) | [JSON](outputs/checks/t002_scientific_checks.json) |
| Main Fig. 3(a-b) | Separable phase map and exceptional-point trajectories with opposite half charges | [PNG](outputs/figures/main_fig3_reproduction.png) | [JSON](outputs/checks/t003_scientific_checks.json) |
| Supplement Fig. 2 | Domain-wall edge-energy surface and exact zero plane | [PNG](outputs/figures/supp_fig2_reproduction.png) | [JSON](outputs/checks/t004_scientific_checks.json) |
| Supplement Fig. 3(a-b) | Paper-exact 80-by-80 cylinder spectra and localized chiral edge branches | [PNG](outputs/figures/supp_fig3_reproduction.png) | [JSON](outputs/checks/t005_scientific_checks.json) |
| Supplement Fig. 4(a-b) | Hybrid exceptional-point sheets and directional exponents one-half and one | [PNG](outputs/figures/supp_fig4_reproduction.png) | [JSON](outputs/checks/t006_scientific_checks.json) |

## Paper Reference vs Independent Reproduction

Each board contains only the numerical figure excerpt needed to audit the independent result against Shen, Zhen, and Fu, Phys. Rev. Lett. 120, 146402 (2018). The reference excerpt and generated result are clearly separated; the excerpt remains outside this repository's open-content license. These boards measure scientific structure and raster presentation, not author-data-level or point-for-point equivalence, and no reference pixel enters numerical generation.

### Main Fig. 1 comparison

![Main Fig. 1 paper reference versus independent reproduction](docs/comparisons/main_fig1_comparison.png)

### Main Fig. 2 comparison

![Main Fig. 2 paper reference versus independent reproduction](docs/comparisons/main_fig2_comparison.png)

### Main Fig. 3 comparison

![Main Fig. 3 paper reference versus independent reproduction](docs/comparisons/main_fig3_comparison.png)

### Supplement Fig. 2 comparison

![Supplement Fig. 2 paper reference versus independent reproduction](docs/comparisons/supp_fig2_comparison.png)

### Supplement Fig. 3 comparison

![Supplement Fig. 3 paper reference versus independent reproduction](docs/comparisons/supp_fig3_comparison.png)

### Supplement Fig. 4 comparison

![Supplement Fig. 4 paper reference versus independent reproduction](docs/comparisons/supp_fig4_comparison.png)

### Main Fig. 1: Complex bulk sheets and independently matched localized domain-wall branch

![Main Fig. 1 reproduction](outputs/figures/main_fig1_reproduction.png)

### Main Fig. 2(a-c): Exceptional-point sheets, loop branch exchange, half vorticity, and square-root cut

![Main Fig. 2(a-c) reproduction](outputs/figures/main_fig2_reproduction.png)

### Main Fig. 3(a-b): Separable phase map and exceptional-point trajectories with opposite half charges

![Main Fig. 3(a-b) reproduction](outputs/figures/main_fig3_reproduction.png)

### Supplement Fig. 2: Domain-wall edge-energy surface and exact zero plane

![Supplement Fig. 2 reproduction](outputs/figures/supp_fig2_reproduction.png)

### Supplement Fig. 3(a-b): Paper-exact 80-by-80 cylinder spectra and localized chiral edge branches

![Supplement Fig. 3(a-b) reproduction](outputs/figures/supp_fig3_reproduction.png)

### Supplement Fig. 4(a-b): Hybrid exceptional-point sheets and directional exponents one-half and one

![Supplement Fig. 4(a-b) reproduction](outputs/figures/supp_fig4_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1706.07435/code
python scripts/run_main_fig1.py
python scripts/run_main_fig2.py
python scripts/run_main_fig3.py
python scripts/run_supp_fig2.py
python scripts/run_supp_fig4.py
python scripts/run_supp_fig3.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 6 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: No author numerical arrays are available, so the scientific score is capped at 90 and does not claim author-data-level equivalence. The initial raster presentation score is 60.28; remaining differences are mainly aspect ratio, 3D camera, typography, and mesh or ink density. Supplement Fig. 1 and Supplement Table I are non-numerical context and are not reproduced as numerical targets.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
