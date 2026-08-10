# 1709.03478: Exploring the Single-Particle Mobility Edge in a One-Dimensional Quasiperiodic Optical Lattice

Preprint: [arXiv:1709.03478 — Exploring the Single-Particle Mobility Edge in a One-Dimensional Quasiperiodic Optical Lattice](https://arxiv.org/abs/1709.03478)

Published as: [Single-Particle Mobility Edge in a One-Dimensional Quasiperiodic Optical Lattice](https://doi.org/10.1103/PhysRevLett.120.160404)

Formal citation: Phys. Rev. Lett. 120, 160404 (2018) · DOI `10.1103/PhysRevLett.120.160404` · Locator `160404`

Public status: **Partial scientific reproduction** · Audit score: **63.55/100**

Exploratory reduced-scale reproduction; no author code, arrays, or pixels were used as numerical input.

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1709.03478/code
python scripts/run_reproduction.py --config config/feature_run.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 5 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Fig. 4 theory is partial and experimental panels are blocked by missing author data.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2b edge density](outputs/figures/fig2b_edge_density.png)

![fig3 theory sweeps](outputs/figures/fig3_theory_sweeps.png)

![fig4 phase boundaries](outputs/figures/fig4_phase_boundaries.png)

![supp fig s1 observables](outputs/figures/supp_fig_s1_observables.png)

![supp fig s2 finite time](outputs/figures/supp_fig_s2_finite_time.png)
