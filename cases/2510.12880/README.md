# 2510.12880: Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain

Preprint: [arXiv:2510.12880 — Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain](https://arxiv.org/abs/2510.12880)

Published as: [Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain](https://doi.org/10.1103/fy4t-6bh8)

Formal citation: Physical Review Letters 137, 046701 (2026) · DOI `10.1103/fy4t-6bh8` · Locator `046701`

Public status: **Historical scientific artifact (4 numerical targets; 4 evidence_compared)** · Audit score: **95.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 4 public generated data files, 2 public generated figures, and 4 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| FIG005A | Squared fidelity of the uniform-positive-w fractionalized MPS with the exact ground state. | [PNG](outputs/figures/ground_state_overlaps.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG005B | Squared fidelity of a one-w-flip MPS with the exact first-excited manifold. | [PNG](outputs/figures/first_excited_overlaps.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG005A: Squared fidelity of the uniform-positive-w fractionalized MPS with the exact ground state.

![FIG005A reproduction](outputs/figures/ground_state_overlaps.png)

### FIG005B: Squared fidelity of a one-w-flip MPS with the exact first-excited manifold.

![FIG005B reproduction](outputs/figures/first_excited_overlaps.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2510.12880/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: V001=evidence_compared, V002=evidence_compared, T001=evidence_compared, T002=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
