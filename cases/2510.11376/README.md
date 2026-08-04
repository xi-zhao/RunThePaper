# 2510.11376: Disorder-Induced Strongly Correlated Photons in Waveguide QED

Preprint: [arXiv:2510.11376 — Disorder-Induced Strongly Correlated Photons in Waveguide QED](https://arxiv.org/abs/2510.11376)

Published as: [Disorder-Induced Strongly Correlated Photons in Waveguide QED](https://doi.org/10.1103/mldt-d59t)

Formal citation: Physical Review Letters 135, 153604 (2025) · DOI `10.1103/mldt-d59t` · Locator `153604`

Public status: **Historical scientific artifact (16 numerical targets; 15 blocked_missing_method, 1 reproduced)** · Audit score: **0.00/100**

Publishes the independently generated numerical artifacts retained by the historical case: 1 public generated data files, 1 public generated figures, and 16 declared numerical targets. The package preserves failed, partial, proxy, and unresolved outcomes instead of upgrading them to completion.

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
| BENCH_EXT | Exact audit of the printed transmission formula and frozen PPB geometry. | [PNG](outputs/figures/idx64_waveguide_gold_audit.png) | [JSON](outputs/checks/similarity_scorecard.json) |

### BENCH_EXT: Exact audit of the printed transmission formula and frozen PPB geometry.

![BENCH_EXT reproduction](outputs/figures/idx64_waveguide_gold_audit.png)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2510.11376/code
python scripts/verify_public_artifacts.py
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: Frozen non-final target states: T_FIG2=blocked_missing_method, T_FIG3=blocked_missing_method, T_FIG4=blocked_missing_method, T_FIG5=blocked_missing_method, T_FIGS0=blocked_missing_method, T_FIGS1=blocked_missing_method, T_FIGS3=blocked_missing_method, T_FIGS4=blocked_missing_method, T_FIGS5=blocked_missing_method, T_FIGS6=blocked_missing_method, T_FIGS7=blocked_missing_method, T_FIGS8=blocked_missing_method, T_FIGS9=blocked_missing_method, T_FIGS10=blocked_missing_method, T_FIGS11=blocked_missing_method. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.
