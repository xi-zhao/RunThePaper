# 10.1103-PhysRevLett.124.113601: Localization Driven Superradiant Instability

Preprint: [1909.08125 — Localization Driven Superradiant Instability](https://arxiv.org/abs/1909.08125)

Published as: [Localization Driven Superradiant Instability](https://doi.org/10.1103/PhysRevLett.124.113601)

Formal citation: Physical Review Letters 124, 113601 (2020) · DOI `10.1103/PhysRevLett.124.113601` · Locator `113601`

Public status: **Partial scientific reproduction** · Audit score: **89.50/100**

Case scaffolded from framework/templates/paper_case.

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

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/10.1103-PhysRevLett.124.113601/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [figures](outputs/figures/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: User selected local Apple M4 execution; no remote accelerator is used. Published PDF and supplement are primary; arXiv v1 source is retained for traceability and source figures.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

![fig2 pixel registered](outputs/figures/fig2_pixel_registered.png)

![fig2 state thresholds](outputs/figures/fig2_state_thresholds.png)

![fig3 mechanism](outputs/figures/fig3_mechanism.png)

![fig3 pixel registered](outputs/figures/fig3_pixel_registered.png)

![fig4 phase response](outputs/figures/fig4_phase_response.png)

![fig4 pixel registered](outputs/figures/fig4_pixel_registered.png)

![fig4b threshold landscape](outputs/figures/fig4b_threshold_landscape.png)

![figs1 density profiles](outputs/figures/figs1_density_profiles.png)

![figs1 pixel registered](outputs/figures/figs1_pixel_registered.png)
