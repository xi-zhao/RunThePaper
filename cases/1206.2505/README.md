# 1206.2505: Dynamical Quantum Phase Transitions in the Transverse-Field Ising Model

Preprint: [arXiv:1206.2505 — Dynamical Quantum Phase Transitions in the Transverse-Field Ising Model](https://arxiv.org/abs/1206.2505)

Published as: [Dynamical Quantum Phase Transitions in the Transverse-Field Ising Model](https://doi.org/10.1103/PhysRevLett.110.135704)

Formal citation: Phys. Rev. Lett. 110, 135704 (2013) · DOI `10.1103/PhysRevLett.110.135704` · Locator `135704`

Public status: **Partial scientific reproduction** · Audit score: **84.29/100**

All published numerical figures have formula-derived code and frozen v7 outputs.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Independent paper assessment](docs/PAPER_ASSESSMENT.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Paper Reference vs Independent Reproduction

Each board contains only the minimum paper excerpt needed for validation and places it beside an independently generated result. Visual agreement is a scientific-region diagnostic, not author-data-level equivalence.

### main fig1 comparison comparison

![main fig1 comparison paper reference versus independent reproduction](docs/comparisons/main_fig1_comparison.png)

### main fig2 comparison comparison

![main fig2 comparison paper reference versus independent reproduction](docs/comparisons/main_fig2_comparison.png)

### main fig3 comparison comparison

![main fig3 comparison paper reference versus independent reproduction](docs/comparisons/main_fig3_comparison.png)

### supp fig1 comparison comparison

![supp fig1 comparison paper reference versus independent reproduction](docs/comparisons/supp_fig1_comparison.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1206.2505/code
python scripts/run_reproduction.py --config config/paper_scale.json --output-root outputs/public_quick_run
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 4 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Fresh-context review is the remaining lifecycle gate.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![main fig1 fisher zeroes](outputs/figures/main_fig1_fisher_zeroes.png)

![main fig2 work rate](outputs/figures/main_fig2_work_rate.png)

![main fig3 magnetization](outputs/figures/main_fig3_magnetization.png)

![supp fig1 postselection](outputs/figures/supp_fig1_postselection.png)
