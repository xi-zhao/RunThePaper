# 2607.00718: Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking

Preprint: [arXiv:2607.00718 — Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking](https://arxiv.org/abs/2607.00718)

Published as: [Enhancing Nonreciprocity through Squeezing-Induced Symmetry Breaking](https://doi.org/10.1103/kh36-7z76)

Formal citation: Phys. Rev. Lett. 136, 253602 (2026) · DOI `10.1103/kh36-7z76` · Locator `253602`

Public status: **Partial scientific reproduction** · Audit score: **90.31/100**

All ten target bundles were executed; Figure S1 is scientifically adjudicated with a rejected quantitative cutoff claim.

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

### fig1c source vs reproduction comparison

![fig1c source vs reproduction paper reference versus independent reproduction](docs/comparisons/fig1c_source_vs_reproduction.png)

### fig2c source vs reproduction comparison

![fig2c source vs reproduction paper reference versus independent reproduction](docs/comparisons/fig2c_source_vs_reproduction.png)

### fig3 source vs reproduction comparison

![fig3 source vs reproduction paper reference versus independent reproduction](docs/comparisons/fig3_source_vs_reproduction.png)

### fig4 source vs reproduction comparison

![fig4 source vs reproduction paper reference versus independent reproduction](docs/comparisons/fig4_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.00718/code
python scripts/run_reproduction.py T001 --device cpu
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 4 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: First milestone targets T001, T002C, T003, and T004. Zenodo transmission arrays appear to belong to an older manuscript version.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1c enhancement](outputs/figures/fig1c_enhancement.png)

![fig2ab dynamics](outputs/figures/fig2ab_dynamics.png)

![fig2c energy enhancement](outputs/figures/fig2c_energy_enhancement.png)

![fig2d ergotropy](outputs/figures/fig2d_ergotropy.png)

![fig3 steady energies](outputs/figures/fig3_steady_energies.png)

![fig4 transmission](outputs/figures/fig4_transmission.png)

![figs1 detuned dynamics](outputs/figures/figs1_detuned_dynamics.png)

![figs2 energy derivatives](outputs/figures/figs2_energy_derivatives.png)

![figs3 energy vs squeezing](outputs/figures/figs3_energy_vs_squeezing.png)

![figs4 passive energy](outputs/figures/figs4_passive_energy.png)
