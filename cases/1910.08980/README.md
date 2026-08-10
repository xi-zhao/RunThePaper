# 1910.08980: Obstacles to State Preparation and Variational Optimization from Symmetry Protection

Preprint: [arXiv:1910.08980 — Obstacles to State Preparation and Variational Optimization from Symmetry Protection](https://arxiv.org/abs/1910.08980)

Published as: [Obstacles to State Preparation and Variational Optimization from Symmetry Protection](https://doi.org/10.1103/PhysRevLett.125.260505)

Formal citation: Physical Review Letters 125, 260505 (2020) · DOI `10.1103/PhysRevLett.125.260505` · Locator `260505`

Public status: **Partial scientific reproduction** · Audit score: **89.00/100**

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

### T001 main fig1 side by side comparison

![T001 main fig1 side by side paper reference versus independent reproduction](docs/comparisons/T001_main_fig1_side_by_side.png)

### T002 main fig1 side by side comparison

![T002 main fig1 side by side paper reference versus independent reproduction](docs/comparisons/T002_main_fig1_side_by_side.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1910.08980/code
python scripts/run_reproduction.py --config config/paper_protocol.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 2 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: All numerical scope is independently reproduced; paper-exact completion is blocked by unpublished random-instance identity and a missing fresh-context review.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 n100](outputs/figures/main_fig1_n100.png)

![main fig1 n32](outputs/figures/main_fig1_n32.png)
