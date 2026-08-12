# 2406.07531: Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids

Preprint: [arXiv:2406.07531 — Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids](https://arxiv.org/abs/2406.07531)

Published as: [Interacting-Bath Dynamical Embedding for Capturing Nonlocal Electron Correlation in Solids](https://doi.org/10.1103/PhysRevLett.133.216402)

Formal citation: Phys. Rev. Lett. 133, 216402 (2024) · DOI `10.1103/PhysRevLett.133.216402` · Locator `volume 133, article 216402`

Public status: **Partial scientific reproduction** · Audit score: **16.00/100**

Nine targets are inventoried and code-ready, while all paper-scale material observables remain compute-deferred.

## Start Here / 从这里开始

- [中文复现 Note](note/reproduction-note.zh-CN.md)
- [English reproduction note](note/reproduction-note.en.md)
- [Equation-level derivation](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Public evidence index](docs/EVIDENCE_INDEX.md)
- [Comparison policy](docs/COMPARISON_POLICY.md)
- [Scientific consistency report](docs/CONSISTENCY_REPORT.md)
- [Paper review protocol](docs/PAPER_REVIEW_PROTOCOL_V2.md)
- [Code and run commands](code/README.md)
- [Machine-readable scorecard](outputs/checks/similarity_scorecard.json)
- [Machine-readable completion boundary](outputs/checks/completion_assessment.json)
- [Derivation (equations)](docs/DERIVATION.md)
- [Numerical methods](docs/NUMERICAL_METHODS.md)
- [Lessons learned](docs/LESSONS_LEARNED.md)

## Quick Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2406.07531/code
python scripts/run_reproduction.py --config config/feature.json
```

Generated files are kept under [data](outputs/data/), [figures](outputs/figures/), and [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, generated figures, public validation checks, and explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: APS supplement returned HTTP 403 locally and through the authorised institutional Jupyter network; Tables S6/S7 remain missing source material. No public author source code or point-level numerical arrays were found in the arXiv archive.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures
