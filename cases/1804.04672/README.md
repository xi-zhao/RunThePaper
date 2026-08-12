# 1804.04672: Non-Hermitian Chern bands

Preprint: [arXiv:1804.04672 — Non-Hermitian Chern bands](https://arxiv.org/abs/1804.04672)

Published as: [Non-Hermitian Chern Bands](https://doi.org/10.1103/PhysRevLett.121.136802)

Formal citation: Physical Review Letters 121, 136802 (2018) · DOI `10.1103/PhysRevLett.121.136802` · Locator `136802`

Public status: **Partial scientific reproduction** · Audit score: **80.18/100**

Reproduces open-boundary and cylinder phase structure, square dynamics, complex spectra, and finite-size checks.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

The left column in each panel is a limited excerpt from Yao et al., [Physical Review Letters 121, 136802 (2018)](https://doi.org/10.1103/PhysRevLett.121.136802); the right column is generated independently from this case. These comparisons validate physical structure and key numerical features, not author-data-level or point-for-point equivalence.

### Fig. 1 comparison

![Fig. 1 paper reference versus independent reproduction](docs/comparisons/fig1_open_boundary_phase_comparison.png)

### Fig. 2 comparison

![Fig. 2 paper reference versus independent reproduction](docs/comparisons/fig2_square_dynamics_comparison.png)

### Fig. 3(a) comparison

![Fig. 3(a) paper reference versus independent reproduction](docs/comparisons/fig3a_cylinder_phase_comparison.png)

### Fig. 3(b) comparison

![Fig. 3(b) paper reference versus independent reproduction](docs/comparisons/fig3b_complex_spectrum_comparison.png)

### Fig. S2 comparison

![Fig. S2 paper reference versus independent reproduction](docs/comparisons/figs2_gap_scaling_comparison.png)

### Fig. S3 comparison

![Fig. S3 paper reference versus independent reproduction](docs/comparisons/figs3_disk_phase_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1804.04672/code
python scripts/run_first_target.py
python scripts/run_open_boundary_phase_diagram.py
python scripts/run_square_dynamics.py
python scripts/run_cylinder_phase_diagram.py
python scripts/run_gap_scaling.py
python scripts/run_disk_phase_diagram.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 6 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Some phase-boundary and panel-level comparisons remain paper-subset or source-table validations rather than full independent finite-size reruns.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![edge branch diagnostic](outputs/figures/edge_branch_diagnostic.png)

![fig1 open boundary phase](outputs/figures/fig1_open_boundary_phase.png)

![fig2 square dynamics](outputs/figures/fig2_square_dynamics.png)

![fig3a cylinder phase](outputs/figures/fig3a_cylinder_phase.png)

![figs2 gap scaling](outputs/figures/figs2_gap_scaling.png)

![figs3 disk phase](outputs/figures/figs3_disk_phase.png)

![first target](outputs/figures/first_target.png)
