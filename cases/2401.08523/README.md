# 2401.08523: Information and Majorization Theory for Fermionic Phase-Space Distributions

Preprint: [arXiv:2401.08523v2 — Information and Majorization Theory for Fermionic Phase-Space Distributions](https://arxiv.org/abs/2401.08523v2)

Published as: [Information and Majorization Theory for Fermionic Phase-Space Distributions](https://doi.org/10.1103/3qg7-r4mq)

Formal citation: Physical Review Letters 135, 110201 (2025) · DOI `10.1103/3qg7-r4mq` · Locator `110201`

Public status: **Historical scientific artifact (2 numerical targets; 2 evidence_compared)** · Audit score: **90.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 3 public generated data files, 2 public generated figures, and 2 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Main Reproduced Results

| Paper item | Reproduced result | Figure | Check |
| --- | --- | --- | --- |
| FIG001 | Occupation of the physical single-mode thermal state across positive and negative temperature branches. | [PNG](outputs/figures/figure_1_fermi_dirac.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG002 | Exact disorder measures and uncertainty bounds of P, W, and Q over the complete physical occupation interval. | [PNG](outputs/figures/figure_2_uncertainty_relations.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG001: Occupation of the physical single-mode thermal state across positive and negative temperature branches.

![FIG001 reproduction](outputs/figures/figure_1_fermi_dirac.png)

### FIG002: Exact disorder measures and uncertainty bounds of P, W, and Q over the complete physical occupation interval.

![FIG002 reproduction](outputs/figures/figure_2_uncertainty_relations.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2401.08523/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: T001=evidence_compared, T002=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
