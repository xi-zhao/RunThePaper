# 1711.09418: Symmetry-resolved entanglement in many-body systems

Preprint: [arXiv:1711.09418 — Symmetry-resolved entanglement in many-body systems](https://arxiv.org/abs/1711.09418)

Published as: [Symmetry-Resolved Entanglement in Many-Body Systems](https://doi.org/10.1103/PhysRevLett.120.200602)

Formal citation: 120, 200602 (2018) · DOI `10.1103/PhysRevLett.120.200602` · Locator `200602`

Public status: **Scientific reproduction — independent review pending** · Audit score: **90.00/100**

All numerical figures reproduced from formulas at paper-declared scale.

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

### T001 fig2 charge resolved comparison

![T001 fig2 charge resolved paper reference versus independent reproduction](docs/comparisons/T001_fig2_charge_resolved.png)

### T002 fig3 entanglement spectrum comparison

![T002 fig3 entanglement spectrum paper reference versus independent reproduction](docs/comparisons/T002_fig3_entanglement_spectrum.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1711.09418/code
python scripts/run_reproduction.py --config config/paper_exact.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 2 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Main Fig. 3 has a confirmed legend mismatch: final curves are sectors 4 and 5, not the printed 5 and 6. Fresh-context independent scientific review is still pending.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 charge resolved reproduction](outputs/figures/fig2_charge_resolved_reproduction.png)

![fig3 entanglement spectrum reproduction](outputs/figures/fig3_entanglement_spectrum_reproduction.png)
