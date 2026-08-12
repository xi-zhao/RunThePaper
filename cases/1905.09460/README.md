# 1905.09460: Topological Phase Transition in Non-Hermitian Quasicrystals

Preprint: [arXiv:1905.09460 — Topological Phase Transition in Non-Hermitian Quasicrystals](https://arxiv.org/abs/1905.09460)

Published as: [Topological Phase Transition in non-Hermitian Quasicrystals](https://doi.org/10.1103/PhysRevLett.122.237601)

Formal citation: Physical Review Letters 122, 237601 (2019) · DOI `10.1103/PhysRevLett.122.237601` · Locator `237601`

Public status: **Partial scientific reproduction** · Audit score: **84.29/100**

Publishes the independently generated numerical artifacts retained by the historical case: 8 public generated data files, 4 public generated figures, and 4 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| FIG001 | Coincident PT, localization, and topological winding transition of the periodic AAH chain. | [PNG](outputs/figures/main_figure_1_topological_transition.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG003 | Laser spectrum broadens across the non-Hermitian transition near Delta_FM=2V0. | [PNG](outputs/figures/main_figure_3_laser_transition.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| SUPP001 | Open-boundary spectra, IPR transition, and edge-localized state counts. | [PNG](outputs/figures/supp_figure_1_edge_effects.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| SUPP002 | Exact and low-reflectance etalon transmission amplitude. | [PNG](outputs/figures/supp_figure_2_etalon_transmission.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG001: Coincident PT, localization, and topological winding transition of the periodic AAH chain.

![FIG001 reproduction](outputs/figures/main_figure_1_topological_transition.png)

### FIG003: Laser spectrum broadens across the non-Hermitian transition near Delta_FM=2V0.

![FIG003 reproduction](outputs/figures/main_figure_3_laser_transition.png)

### SUPP001: Open-boundary spectra, IPR transition, and edge-localized state counts.

![SUPP001 reproduction](outputs/figures/supp_figure_1_edge_effects.png)

### SUPP002: Exact and low-reflectance etalon transmission amplitude.

![SUPP002 reproduction](outputs/figures/supp_figure_2_etalon_transmission.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1905.09460/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: T001=evidence_compared, T002=partially_reproduced, T003=partially_reproduced, T004=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
