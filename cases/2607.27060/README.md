# 2607.27060: Optimising Trotter-Suzuki Simulations of Markovian Open Quantum Systems via Classical Search

Preprint: [arXiv:2607.27060v1 — Optimising Trotter-Suzuki Simulations of Markovian Open Quantum Systems via Classical Search](https://arxiv.org/abs/2607.27060v1)

Formal publication: **Not recorded as of 2026-08-04**

Public status: **Scientific reproduction — invalid** · Audit score: **90.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 8 public generated data files, 8 public generated figures, and 8 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| FIG002A | XX-chain first-order deterministic resource bounds. | [PNG](outputs/figures/fig002a_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG002B | XX-chain first-order randomised resource bounds. | [PNG](outputs/figures/fig002b_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG002C | XX-chain second-order deterministic resource bounds. | [PNG](outputs/figures/fig002c_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG002D | XX-chain second-order randomised resource bounds. | [PNG](outputs/figures/fig002d_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG003A | TFIM first-order deterministic resource bounds. | [PNG](outputs/figures/fig003a_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG003B | TFIM first-order randomised resource bounds. | [PNG](outputs/figures/fig003b_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG003C | TFIM second-order deterministic resource bounds. | [PNG](outputs/figures/fig003c_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |
| FIG003D | TFIM second-order randomised resource bounds. | [PNG](outputs/figures/fig003d_panel.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG002A: XX-chain first-order deterministic resource bounds.

![FIG002A reproduction](outputs/figures/fig002a_panel.png)

### FIG002B: XX-chain first-order randomised resource bounds.

![FIG002B reproduction](outputs/figures/fig002b_panel.png)

### FIG002C: XX-chain second-order deterministic resource bounds.

![FIG002C reproduction](outputs/figures/fig002c_panel.png)

### FIG002D: XX-chain second-order randomised resource bounds.

![FIG002D reproduction](outputs/figures/fig002d_panel.png)

### FIG003A: TFIM first-order deterministic resource bounds.

![FIG003A reproduction](outputs/figures/fig003a_panel.png)

### FIG003B: TFIM first-order randomised resource bounds.

![FIG003B reproduction](outputs/figures/fig003b_panel.png)

### FIG003C: TFIM second-order deterministic resource bounds.

![FIG003C reproduction](outputs/figures/fig003c_panel.png)

### FIG003D: TFIM second-order randomised resource bounds.

![FIG003D reproduction](outputs/figures/fig003d_panel.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2607.27060/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
