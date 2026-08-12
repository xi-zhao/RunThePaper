# 2606.30255: Photonic Violation of Wigner's Inequality

Preprint: [arXiv:2606.30255v1 — Photonic Violation of Wigner's Inequality](https://arxiv.org/abs/2606.30255v1)

Formal publication: **Not recorded as of 2026-08-04**

Public status: **Scientific reproduction — invalid** · Audit score: **90.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 4 public generated data files, 4 public generated figures, and 4 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| FIG003 | Density-matrix Wigner value and its three Born-probability components versus symmetric relative angle. | [PNG](outputs/figures/fig003_theory.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG004 | Density-matrix Wigner value and its components under a common rotation of both measurement bases. | [PNG](outputs/figures/fig004_theory.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG005A | Density-matrix Wigner value and components while Alice is fixed and Bob's basis rotates. | [PNG](outputs/figures/fig005a_theory.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG005B | Density-matrix Wigner value and components while Bob is fixed and Alice's basis rotates. | [PNG](outputs/figures/fig005b_theory.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG003: Density-matrix Wigner value and its three Born-probability components versus symmetric relative angle.

![FIG003 reproduction](outputs/figures/fig003_theory.png)

### FIG004: Density-matrix Wigner value and its components under a common rotation of both measurement bases.

![FIG004 reproduction](outputs/figures/fig004_theory.png)

### FIG005A: Density-matrix Wigner value and components while Alice is fixed and Bob's basis rotates.

![FIG005A reproduction](outputs/figures/fig005a_theory.png)

### FIG005B: Density-matrix Wigner value and components while Bob is fixed and Alice's basis rotates.

![FIG005B reproduction](outputs/figures/fig005b_theory.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2606.30255/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
