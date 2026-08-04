# 2505.00079: Emergent photons and mechanisms of confinement

Preprint: [arXiv:2505.00079 — Emergent photons and mechanisms of confinement](https://arxiv.org/abs/2505.00079)

Published as: [Emergent Photons and Confinement: A Numerical Study on <mml:math xmlns:mml="http://www.w3.org/1998/Math/MathML" display="inline"> <mml:mrow> <mml:msub> <mml:mrow> <mml:mi mathvariant="double-struck">Z</mml:mi> </mml:mrow> <mml:mrow> <mml:mi>N</mml:mi> </mml:mrow> </mml:msub> </mml:mrow> </mml:math> Lattice Gauge Theory](https://doi.org/10.1103/h8mn-t4fk)

Formal citation: Physical Review Letters 135, 221901 (2025) · DOI `10.1103/h8mn-t4fk` · Locator `221901`

Public status: **Historical scientific artifact (8 numerical targets; 3 blocked_compute_scale, 1 failed, 4 partially_reproduced)** · Audit score: **30.20/100**

Publishes the independently generated numerical artifacts retained by the historical case: 5 public generated data files, 1 public generated figures, and 8 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| FIG002 | Z7 Polyakov order parameter and defect ordering across beta. | [PNG](outputs/figures/idx56_benchmark_results.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### FIG002: Z7 Polyakov order parameter and defect ordering across beta.

![FIG002 reproduction](outputs/figures/idx56_benchmark_results.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install torch
cd cases/2505.00079/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: T001=partially_reproduced, T002=partially_reproduced, T003=partially_reproduced, T004=failed, T005=partially_reproduced, T006=blocked_compute_scale, T007=blocked_compute_scale, T008=blocked_compute_scale. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
