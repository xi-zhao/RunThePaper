# physics-0206018: Boundary element method for resonances in dielectric microcavities

Preprint: [arXiv:physics/0206018 — Boundary element method for resonances in dielectric microcavities](https://arxiv.org/abs/physics/0206018)

Published as: [Boundary element method for resonances in dielectric microcavities](https://doi.org/10.1088/1464-4258/5/1/308)

Formal citation: Journal of Optics A: Pure and Applied Optics 5, 53–60 (2003) · DOI `10.1088/1464-4258/5/1/308` · Locator `53–60`

Public status: **Reduced-scale reproduction of all numerical figures** · Audit score: **50.49/100**

Independently implements the paper's boundary-element equations and regenerates all and only its numerical figures: the scattering cross section, resonant near field, and far-field radiation pattern. All three targets pass independent physical checks.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Similarity scorecard](docs/SIMILARITY_SCORECARD.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| Fig. 5 | Plane-wave scattering cross section and resonance sequence | [PNG](outputs/figures/fig5_render_contract.png) | [JSON](outputs/checks/fig5_science.json) |
| Fig. 6 | Resonant near-field intensity from the generated boundary state | [PNG](outputs/figures/fig6_render_contract.png) | [JSON](outputs/checks/fig6_science.json) |
| Fig. 7 | Far-field radiation from the same generated boundary state | [PNG](outputs/figures/fig7_render_contract.png) | [JSON](outputs/checks/fig7_science.json) |

### Fig. 5: Plane-wave scattering cross section and resonance sequence

![Fig. 5 reproduction](outputs/figures/fig5_render_contract.png)

### Fig. 6: Resonant near-field intensity from the generated boundary state

![Fig. 6 reproduction](outputs/figures/fig6_render_contract.png)

### Fig. 7: Far-field radiation from the same generated boundary state

![Fig. 7 reproduction](outputs/figures/fig7_render_contract.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/physics-0206018/code
python scripts/run_all.py
python scripts/render_figures.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The feature run uses 432 constant boundary elements rather than the paper's 1600 because the exact corner-rounding curve and nonuniform element map are not published; narrow resonance and far-field peaks therefore retain mesh-dependent shifts.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
