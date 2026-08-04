# 1810.05651: Probing context-dependent errors in quantum processors

Preprint: [arXiv:1810.05651 — Probing context-dependent errors in quantum processors](https://arxiv.org/abs/1810.05651)

Published as: [Probing Context-Dependent Errors in Quantum Processors](https://doi.org/10.1103/PhysRevX.9.021045)

Formal citation: Physical Review X 9, 021045 (2019) · DOI `10.1103/PhysRevX.9.021045` · Locator `021045`

Public status: **Historical scientific artifact (2 numerical targets; 2 reproduced)** · Audit score: **100.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 4 public generated data files, 2 public generated figures, and 2 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| FIG002 | Detection strength and circuit-localized magnitude of simulated gate-angle drift. | [PNG](outputs/figures/fig2_reproduction.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG003 | Maximum statistically significant change in Q15 outcome probabilities while each IBM CNOT rung is driven. | [PNG](outputs/figures/fig3_reproduction.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG002: Detection strength and circuit-localized magnitude of simulated gate-angle drift.

![FIG002 reproduction](outputs/figures/fig2_reproduction.png)

### FIG003: Maximum statistically significant change in Q15 outcome probabilities while each IBM CNOT rung is driven.

![FIG003 reproduction](outputs/figures/fig3_reproduction.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/1810.05651/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The legacy case has no machine-verifiable author-code isolation attestation. The statistical reproduction consumes released experimental count data; it is not a first-principles simulation of the hardware experiment. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
