# 2607.08767: Plaquette: A hardware-aware design platform for fault-tolerant quantum computers

Preprint: [arXiv:2607.08767 — Plaquette: A hardware-aware design platform for fault-tolerant quantum computers](https://arxiv.org/abs/2607.08767)

Formal publication: **Not recorded as of 2026-08-04**

Public status: **Historical scientific artifact (1 numerical target; 1 failed)** · Audit score: **45.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 1 public generated data files, 1 public generated figures, and 1 declared numerical target. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| Fig. 5(a) coherent over-rotation | The exact Plaquette repetition-memory circuit locations, frame convention, and decoder graph are unpublished; the coherent result is 0.9052 instead of 0.387. | [PNG](outputs/figures/fig5a_proxy_results.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### Fig. 5(a) coherent over-rotation: The exact Plaquette repetition-memory circuit locations, frame convention, and decoder graph are unpublished; the coherent result is 0.9052 instead of 0.387.

![Fig. 5(a) coherent over-rotation reproduction](outputs/figures/fig5a_proxy_results.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install qiskit qiskit-aer
cd cases/2607.08767/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: F5A_PROXY=failed. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
