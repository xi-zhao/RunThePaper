# 2608.05312: Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport

Preprint: [arXiv:2608.05312v1 — Unidirectional Dark-to-Bright Rescue in Cavity-Coupled Quantum Transport](https://arxiv.org/abs/2608.05312)

Formal publication: **Not recorded as of 2026-08-08**

Public status: **Partial scientific reproduction** · Audit score: **83.52/100**

Eleven independent numerical targets reproduce the paper's central features; only the four T011 QCLE benchmark series remain uncovered because indispensable operating parameters are not published.

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

### fig2 source vs reproduction comparison

![fig2 source vs reproduction paper reference versus independent reproduction](docs/comparisons/fig2_source_vs_reproduction.png)

### fig3 source vs reproduction comparison

![fig3 source vs reproduction paper reference versus independent reproduction](docs/comparisons/fig3_source_vs_reproduction.png)

### figS1 source vs reproduction comparison

![figS1 source vs reproduction paper reference versus independent reproduction](docs/comparisons/figS1_source_vs_reproduction.png)

### figS2 source vs reproduction comparison

![figS2 source vs reproduction paper reference versus independent reproduction](docs/comparisons/figS2_source_vs_reproduction.png)

### figS3 source vs reproduction comparison

![figS3 source vs reproduction paper reference versus independent reproduction](docs/comparisons/figS3_source_vs_reproduction.png)

### figS4 source vs reproduction comparison

![figS4 source vs reproduction paper reference versus independent reproduction](docs/comparisons/figS4_source_vs_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2608.05312/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes, and 7 limited comparison panels. Those panels use the minimum paper excerpts needed for validation and clearly separate the paper reference from the independent result. The case does not redistribute the paper PDF, arXiv source archive, standalone original figures, EPS paths, digitized source curves, or source-derived point sets.

Remaining limitation: Mean hopping t=1 meV and source state |1> are reconstructed from cross-figure constraints and validated numerically. Exact author random seeds and optimization grids are unavailable, so generated artifacts are exploratory paper-subset evidence. Ten scored numerical targets pass with an overall similarity score of 83.4; the QCLE benchmark remains blocked by missing source inputs.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig1c size scaling](outputs/figures/fig1c_size_scaling.png)

![fig2 reproduction](outputs/figures/fig2_reproduction.png)

![fig3 temperature](outputs/figures/fig3_temperature.png)

![figS1 site n sweep](outputs/figures/figS1_site_n_sweep.png)

![figS2 scaling laws](outputs/figures/figS2_scaling_laws.png)

![figS3 site n dynamics](outputs/figures/figS3_site_n_dynamics.png)

![figS4 temperature n64](outputs/figures/figS4_temperature_n64.png)

![figS1 site n sweep](outputs/figures/final_disposition/figS1_site_n_sweep.png)

![figS1 site n sweep](outputs/figures/implementation_probe/figS1_site_n_sweep.png)
