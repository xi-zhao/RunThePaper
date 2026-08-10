# 1807.02414: Hydrodynamic Diffusion in Integrable Systems

Preprint: [arXiv:1807.02414 — Hydrodynamic Diffusion in Integrable Systems](https://arxiv.org/abs/1807.02414)

Published as: [Hydrodynamic Diffusion in Integrable Systems](https://doi.org/10.1103/PhysRevLett.121.160603)

Formal citation: Phys. Rev. Lett. 121, 160603 (2018) · DOI `10.1103/PhysRevLett.121.160603` · Locator `121, 160603`

Public status: **Partial scientific reproduction** · Audit score: **84.36/100**

Independent TBA reproduces the six theory curves and text values; the full spectral diffusion operator and external tDMRG remain open.

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

### T001 side by side and difference comparison

![T001 side by side and difference paper reference versus independent reproduction](docs/comparisons/T001_side_by_side_and_difference.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1807.02414/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 1 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: The solid curves use a declared collective-spin projection of the full spectral diffusion operator. External tDMRG markers are deferred and were not digitized or copied.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![T001 fig1 domain wall](outputs/figures/T001_fig1_domain_wall.png)

![T002 diffusion constants](outputs/figures/T002_diffusion_constants.png)
