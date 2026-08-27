# 10.1038-s41586-026-10720-3: Backreaction of stimulated Hawking radiation in an optical analogue

Preprint: [arXiv:2607.01118 — Backreaction of stimulated Hawking radiation in an optical analogue](https://arxiv.org/abs/2607.01118)

Published as: [Backreaction of stimulated Hawking radiation in an optical analogue](https://doi.org/10.1038/s41586-026-10720-3)

Formal citation: Nature 655, 336-341 (2026) · DOI `10.1038/s41586-026-10720-3` · Locator `336-341`

Public status: **Partial scientific reproduction** · Audit score: **26.54/100**

The 28-item audit identifies 13 theoretical targets, 13 experimental reference items, and two schematics; theoretical coverage is 13/13 and lifecycle is partial.

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
pip install torch
cd cases/10.1038-s41586-026-10720-3/code
python scripts/run_reproduction.py
```

Published machine-readable artifacts are kept under [data](outputs/data/), [checks](outputs/checks/).

## Reproduction Boundary

This public case includes paper-derived code, generated data, public validation checks, explanatory notes. It does not redistribute the paper PDF, arXiv source archive, original figures, EPS paths, digitized source curves, source-derived point sets, or source-vs-generated composite panels.

Remaining limitation: The measured fibre dispersion coefficients, fitted frame corrections, six Fig. 4 parameter tables, raw spectra, raw fluxes, and measured pulse states are unavailable. The 47-unit paper profile is code-ready; a 17-unit CPU smoke profile completed with isolated file-access attestation. The formula-only PCF surrogate does not recover the printed 1551 nm horizon, so it is recorded as a missing-parameter/model-mismatch boundary rather than a paper error. Historical vector-trace fits, marker regressions, pixel scores, and UPPE outputs based on the traced dispersion are retained only as comparison history and are ineligible as scientific evidence. No author scientific code, author numerical arrays, digitized curves, or source pixels enter the formula-only numerical runner. The public projection and publish manifest have not yet been refreshed from this calibration state.

Final-parameter rule: final public figures use the paper parameters when feasible. Any reduced-scale, subset, proxy, or blocked target must be labeled explicitly and cannot be presented as a complete reproduction.

## Generated Figures

No generated figure is published at the current partial boundary.
